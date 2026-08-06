import os
import uuid
import logging
from datetime import datetime
import anyio
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.presentation.dependencies.auth_dependency import get_current_user
from app.infrastructure.database.database import get_db
from app.infrastructure.queue import analysis_queue, AnalysisTask
from app.data.analysis_repository import AnalysisRepository, CLOUD_NAME_MAPPING

REVERSE_CLOUD_NAME_MAPPING = {v: k for k, v in CLOUD_NAME_MAPPING.items()}

router = APIRouter()
logger = logging.getLogger(__name__)

USER_ID_NOT_FOUND_MSG = "User ID not found in token"
UPLOADS_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads"))
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
JPEG_SIGNATURE = b"\xff\xd8\xff"
ALLOWED_JPEG_EXTENSIONS = {".jpg", ".jpeg"}
JPEG_CONTENT_TYPE = "image/jpeg"

def _validate_uploaded_jpeg(file: UploadFile, content: bytes):
    if len(content) == 0:
        logger.warning("Image upload rejected because file is empty")
        raise HTTPException(status_code=400, detail="IMAGE_EMPTY")

    if len(content) > MAX_IMAGE_SIZE_BYTES:
        logger.warning(
            "Image upload rejected due to size limit size_bytes=%s max_bytes=%s",
            len(content),
            MAX_IMAGE_SIZE_BYTES,
        )
        raise HTTPException(status_code=413, detail="IMAGE_TOO_LARGE_MAX_5MB")

    file_ext = os.path.splitext(file.filename or "")[1].lower()
    content_type = (file.content_type or "").lower()
    has_valid_extension = file_ext in ALLOWED_JPEG_EXTENSIONS
    has_valid_content_type = not content_type or content_type == JPEG_CONTENT_TYPE
    has_jpeg_signature = content.startswith(JPEG_SIGNATURE)

    if not (has_valid_extension and has_valid_content_type and has_jpeg_signature):
        logger.warning("Image upload rejected due to invalid JPG format")
        raise HTTPException(status_code=400, detail="INVALID_IMAGE_FORMAT_JPG_ONLY")

@router.get("/upload", responses={403: {"description": "Forbidden"}, 405: {"description": "Method Not Allowed"}})
def upload_image_get_requires_auth(
    user: Annotated[dict, Depends(get_current_user)]
):
    raise HTTPException(status_code=405, detail="Use POST to upload an image")

@router.post("/upload", responses={400: {"description": "Invalid image"}, 401: {"description": "Unauthorized"}, 413: {"description": "Payload Too Large"}})
async def upload_image(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File(...)],
    location: Annotated[str, Form()] = "Ubicación desconocida",
    latitude: Annotated[float | None, Form()] = None,
    longitude: Annotated[float | None, Form()] = None,
    fcm_token: Annotated[str, Form()] = "",
    include_explainability: Annotated[bool, Form()] = False
):
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail=USER_ID_NOT_FOUND_MSG)

    content = await file.read()
    _validate_uploaded_jpeg(file, content)

    file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{file_ext}"
    
    user_uploads_dir = os.path.join(UPLOADS_BASE_DIR, uid)
    await anyio.Path(user_uploads_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(user_uploads_dir, unique_filename)

    async with await anyio.open_file(file_path, "wb") as f:
        await f.write(content)
        
    image_db_path = f"/uploads/{uid}/{unique_filename}"
    
    firebase_claim = user.get("firebase", {})
    is_anon = firebase_claim.get("sign_in_provider") == "anonymous"
    
    repository = AnalysisRepository(db)
    analysis_id = repository.create_analysis(
        uid=uid,
        image_path=image_db_path,
        location=location,
        latitude=latitude,
        longitude=longitude,
        is_anon=is_anon,
    )
    db.commit()
    
    task = AnalysisTask(analysis_id=analysis_id, file_path=file_path, fcm_token=fcm_token, explainability=include_explainability)
    await analysis_queue.put(task)
    logger.info("Queued new analysis task analysis_id=%s uid=%s", analysis_id, uid)
    
    return {
        "message": "Imagen recibida correctamente. Iniciando análisis...",
        "status": "analyzing",
        "analysis_id": analysis_id
    }

def _initialize_analysis_record(row, analysis_id: str) -> dict:
    analysis_datetime = row.datetime
    if hasattr(analysis_datetime, "isoformat"):
        analysis_date = analysis_datetime.isoformat() + "Z"
    else:
        analysis_date = f"{analysis_datetime}Z" if analysis_datetime else None

    return {
        "id": analysis_id,
        "status": row.status,
        "date": analysis_date,
        "location": row.location or "Ubicación desconocida",
        "latitude": row.latitude,
        "longitude": row.longitude,
        "imageUrl": row.image_path,
        "results": {
            "cloudTypes": [],
            "cloudDetails": [],
            "forecast": "",
            "warnings": []
        }
    }

def _update_cloud_details(res: dict, row):
    if not row.cloud_type:
        return
        
    cloud_key = REVERSE_CLOUD_NAME_MAPPING.get(row.cloud_type, row.cloud_type)
    has_box = row.box_ymin is not None and row.box_xmin is not None and row.box_ymax is not None and row.box_xmax is not None
    
    if has_box:
        res["cloudDetails"].append({
            "type": cloud_key,
            "originalType": row.cloud_type,
            "box": [row.box_ymin, row.box_xmin, row.box_ymax, row.box_xmax]
        })
        # Remove any previous detail for this type that had no box, if we now have one
        res["cloudDetails"] = [d for d in res["cloudDetails"] if not (d.get("type") == cloud_key and d.get("box") is None)]
    elif not any(d.get("type") == cloud_key for d in res["cloudDetails"]):
        res["cloudDetails"].append({
            "type": cloud_key,
            "originalType": row.cloud_type,
            "box": None
        })

def _update_forecast_and_warnings(res: dict, row):
    if row.forecast and row.forecast not in res["forecast"]:
        res["forecast"] = (res["forecast"] + " " + row.forecast).strip()
        
    if getattr(row, 'warning', None):
        warning_exists = any(w.get("text") == row.warning for w in res["warnings"])
        if not warning_exists:
            res["warnings"].append({
                "type": REVERSE_CLOUD_NAME_MAPPING.get(row.cloud_type, row.cloud_type) if row.cloud_type else None,
                "text": row.warning,
                "level": getattr(row, "warning_level", 0)
            })

def _update_analysis_results(res: dict, row):
    if row.cloud_type:
        cloud_key = REVERSE_CLOUD_NAME_MAPPING.get(row.cloud_type, row.cloud_type)
        if cloud_key not in res["cloudTypes"]:
            res["cloudTypes"].append(cloud_key)
        
    _update_cloud_details(res, row)
    _update_forecast_and_warnings(res, row)

@router.get("/history", responses={401: {"description": "Unauthorized"}})
def get_analysis_history(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail=USER_ID_NOT_FOUND_MSG)

    result = AnalysisRepository(db).get_history_rows(uid)
    
    analyses_dict = {}
    
    for row in result:
        analysis_id = str(row.id)
        if analysis_id not in analyses_dict:
            analyses_dict[analysis_id] = _initialize_analysis_record(row, analysis_id)
            
        _update_analysis_results(analyses_dict[analysis_id]["results"], row)
            
    # List of analyses, maintaining the descending order
    return list(analyses_dict.values())

def _remove_analysis_file(image_path):
    if not image_path:
        return
    # image_path is expected to be like /uploads/{uid}/{filename}
    rel_path = image_path.replace("/uploads/", "")
    file_path = os.path.join(UPLOADS_BASE_DIR, rel_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.exception("Error removing analysis file at %s: %s", file_path, e)

@router.delete("/user-data", responses={401: {"description": "Unauthorized"}})
def delete_user_data(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail=USER_ID_NOT_FOUND_MSG)

    image_paths = AnalysisRepository(db).delete_user_analyses(uid)
    for image_path in image_paths:
        _remove_analysis_file(image_path)

    db.commit()
    logger.info("Deleted all analysis data for uid=%s", uid)
    
    return {"message": "Datos de usuario eliminados correctamente."}

@router.delete("/{analysis_id}", responses={401: {"description": "Unauthorized"}, 404: {"description": "Not Found"}})
def delete_single_analysis(
    analysis_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail=USER_ID_NOT_FOUND_MSG)

    image_path = AnalysisRepository(db).delete_analysis(analysis_id, uid)
    if image_path is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    _remove_analysis_file(image_path)
    db.commit()
    logger.info("Deleted single analysis analysis_id=%s uid=%s", analysis_id, uid)
    
    return {"message": "Análisis eliminado correctamente."}

@router.patch("/{analysis_id}/cancel", responses={400: {"description": "Bad Request"}, 401: {"description": "Unauthorized"}, 404: {"description": "Not Found"}})
def cancel_analysis(
    analysis_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail=USER_ID_NOT_FOUND_MSG)

    result = AnalysisRepository(db).cancel_analysis(analysis_id, uid)
    if result == AnalysisRepository.CANCEL_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if result == AnalysisRepository.CANCEL_INVALID_STATUS:
        raise HTTPException(status_code=400, detail="Only 'analyzing' tasks can be cancelled")

    db.commit()
    logger.info("Cancelled analysis analysis_id=%s uid=%s", analysis_id, uid)
    
    return {"message": "Análisis cancelado correctamente."}

@router.get(
    "/{analysis_id}/cancel",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        405: {"description": "Method Not Allowed"},
    },
)
def cancel_analysis_get_requires_auth(
    analysis_id: int,
    user: Annotated[dict, Depends(get_current_user)]
):
    raise HTTPException(status_code=405, detail="Use PATCH to cancel an analysis")
