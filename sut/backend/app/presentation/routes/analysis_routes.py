import os
import uuid
import logging
from datetime import datetime, timezone
import anyio
from typing import Annotated, Literal
from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.presentation.dependencies.auth_dependency import get_current_user
from app.infrastructure.database.database import get_db
from app.infrastructure.queue import analysis_queue, AnalysisTask
from app.data.analysis_repository import AnalysisRepository, CLOUD_NAME_MAPPING

REVERSE_CLOUD_NAME_MAPPING = {v: k for k, v in CLOUD_NAME_MAPPING.items()}

router = APIRouter()
logger = logging.getLogger(__name__)

USER_ID_NOT_FOUND_MSG = "USER_ID_NOT_FOUND"
UPLOADS_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads"))
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
JPEG_SIGNATURE = b"\xff\xd8\xff"
ALLOWED_JPEG_EXTENSIONS = {".jpg", ".jpeg"}
JPEG_CONTENT_TYPE = "image/jpeg"

AUTH_RESPONSE = {"description": "NOT_AUTHENTICATED / INVALID_TOKEN / USER_ID_NOT_FOUND"}


def _validate_uploaded_jpeg(file: UploadFile, content: bytes):
    if len(content) == 0:
        logger.warning("Image upload rejected because file is empty")
        raise HTTPException(status_code=422, detail="IMAGE_EMPTY")

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
        raise HTTPException(status_code=415, detail="INVALID_IMAGE_FORMAT_JPG_ONLY")


class AnalysisPatch(BaseModel):
    status: Literal["cancelled"]


def _require_uid(user: dict) -> str:
    uid = user.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail=USER_ID_NOT_FOUND_MSG)
    return uid


@router.post(
    "",
    status_code=202,
    responses={
        202: {"description": "Accepted; analysis queued. The Location header points to the new analysis."},
        401: AUTH_RESPONSE,
        413: {"description": "IMAGE_TOO_LARGE_MAX_5MB"},
        415: {"description": "INVALID_IMAGE_FORMAT_JPG_ONLY"},
        422: {"description": "IMAGE_EMPTY or invalid form data"},
    },
)
async def create_analysis(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    response: Response,
    file: Annotated[UploadFile, File(...)],
    location: Annotated[str, Form()] = "Ubicación desconocida",
    latitude: Annotated[float | None, Form()] = None,
    longitude: Annotated[float | None, Form()] = None,
    fcm_token: Annotated[str, Form(alias="fcmToken")] = "",
    include_explainability: Annotated[bool, Form(alias="includeExplainability")] = False
):
    uid = _require_uid(user)

    content = await file.read()
    _validate_uploaded_jpeg(file, content)

    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"

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

    response.headers["Location"] = f"/api/v1/analyses/{analysis_id}"
    return {"id": analysis_id, "status": "analyzing"}


def _format_utc(value) -> str | None:
    """Return a UTC ISO-8601 string ending in 'Z'.

    Stored values are naive UTC (see AnalysisRepository.create_analysis); SQLite
    returns them as strings, PostgreSQL as datetime. Aware values are converted.
    """
    if not value:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat() + "Z"


def _initialize_analysis_record(row, analysis_id: int) -> dict:
    return {
        "id": analysis_id,
        "status": row.status,
        "date": _format_utc(row.datetime),
        "location": row.location or "Ubicación desconocida",
        "latitude": row.latitude,
        "longitude": row.longitude,
        "imageUrl": f"/api/v1/analyses/{analysis_id}/image",
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


def _build_analyses(rows) -> list[dict]:
    analyses_dict = {}
    for row in rows:
        if row.id not in analyses_dict:
            analyses_dict[row.id] = _initialize_analysis_record(row, row.id)
        _update_analysis_results(analyses_dict[row.id]["results"], row)
    # dict preserves insertion order, i.e. the descending order of the query
    return list(analyses_dict.values())


@router.get(
    "",
    responses={
        200: {
            "description": "Analyses, newest first. The X-Total-Count header carries the user's total.",
            "headers": {"X-Total-Count": {"schema": {"type": "integer"}}},
        },
        401: AUTH_RESPONSE,
    },
)
def list_analyses(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    response: Response,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
):
    uid = _require_uid(user)
    repository = AnalysisRepository(db)
    rows = repository.get_history_rows(uid, limit=size, offset=page * size)
    response.headers["X-Total-Count"] = str(repository.count_user_analyses(uid))
    return _build_analyses(rows)


@router.get(
    "/{analysis_id}",
    responses={401: AUTH_RESPONSE, 404: {"description": "ANALYSIS_NOT_FOUND"}},
)
def get_analysis(
    analysis_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    uid = _require_uid(user)
    analyses = _build_analyses(AnalysisRepository(db).get_analysis_rows(analysis_id, uid))
    if not analyses:
        raise HTTPException(status_code=404, detail="ANALYSIS_NOT_FOUND")
    return analyses[0]


def _resolve_upload_path(image_path: str | None) -> str | None:
    """Map a stored image_path to a file inside UPLOADS_BASE_DIR, or None if it escapes it."""
    if not image_path:
        return None
    rel_path = image_path.replace("/uploads/", "", 1).lstrip("/\\")
    base = os.path.realpath(UPLOADS_BASE_DIR)
    candidate = os.path.realpath(os.path.join(base, rel_path))
    if os.path.commonpath([base, candidate]) != base:
        return None
    return candidate


@router.get(
    "/{analysis_id}/image",
    response_class=FileResponse,
    responses={
        200: {"content": {JPEG_CONTENT_TYPE: {}}, "description": "The analyzed JPEG image"},
        401: AUTH_RESPONSE,
        404: {"description": "ANALYSIS_NOT_FOUND or IMAGE_NOT_FOUND"},
    },
)
def get_analysis_image(
    analysis_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    uid = _require_uid(user)
    rows = AnalysisRepository(db).get_analysis_rows(analysis_id, uid)
    if not rows:
        raise HTTPException(status_code=404, detail="ANALYSIS_NOT_FOUND")
    file_path = _resolve_upload_path(rows[0].image_path)
    if file_path is None or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="IMAGE_NOT_FOUND")
    return FileResponse(file_path, media_type=JPEG_CONTENT_TYPE)


def _remove_analysis_file(image_path):
    if not image_path:
        return
    # image_path is expected to be like /uploads/{uid}/{filename}
    file_path = _resolve_upload_path(image_path)
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.exception("Error removing analysis file at %s: %s", file_path, e)


@router.delete(
    "",
    status_code=204,
    responses={204: {"description": "All analyses of the caller deleted"}, 401: AUTH_RESPONSE},
)
def delete_all_analyses(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = _require_uid(user)

    image_paths = AnalysisRepository(db).delete_user_analyses(uid)
    for image_path in image_paths:
        _remove_analysis_file(image_path)

    db.commit()
    logger.info("Deleted all analysis data for uid=%s", uid)
    return Response(status_code=204)


@router.delete(
    "/{analysis_id}",
    status_code=204,
    responses={204: {"description": "Analysis deleted"}, 401: AUTH_RESPONSE, 404: {"description": "ANALYSIS_NOT_FOUND"}},
)
def delete_analysis(
    analysis_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = _require_uid(user)

    image_path = AnalysisRepository(db).delete_analysis(analysis_id, uid)
    if image_path is None:
        raise HTTPException(status_code=404, detail="ANALYSIS_NOT_FOUND")

    _remove_analysis_file(image_path)
    db.commit()
    logger.info("Deleted single analysis analysis_id=%s uid=%s", analysis_id, uid)
    return Response(status_code=204)


@router.patch(
    "/{analysis_id}",
    responses={
        401: AUTH_RESPONSE,
        404: {"description": "ANALYSIS_NOT_FOUND"},
        409: {"description": "ANALYSIS_NOT_CANCELLABLE (analysis is not in 'analyzing')"},
        422: {"description": "Body status is not 'cancelled'"},
    },
)
def update_analysis(
    analysis_id: int,
    body: AnalysisPatch,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    uid = _require_uid(user)

    repository = AnalysisRepository(db)
    result = repository.cancel_analysis(analysis_id, uid)
    if result == AnalysisRepository.CANCEL_NOT_FOUND:
        raise HTTPException(status_code=404, detail="ANALYSIS_NOT_FOUND")

    if result == AnalysisRepository.CANCEL_INVALID_STATUS:
        raise HTTPException(status_code=409, detail="ANALYSIS_NOT_CANCELLABLE")

    db.commit()
    logger.info("Cancelled analysis analysis_id=%s uid=%s", analysis_id, uid)
    return _build_analyses(repository.get_analysis_rows(analysis_id, uid))[0]
