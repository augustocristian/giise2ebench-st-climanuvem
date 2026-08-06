from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.presentation.routes.analysis_routes import (
    router,
    _validate_uploaded_jpeg,
    _initialize_analysis_record,
    _update_analysis_results,
)


def test_initialize_analysis_record_uses_defaults_for_missing_values():
    row = SimpleNamespace(
        status="completed",
        datetime=None,
        location=None,
        latitude=None,
        longitude=None,
        image_path=None,
    )

    record = _initialize_analysis_record(row, "12")

    assert record["id"] == "12"
    assert record["date"] is None
    assert record["location"] == "Ubicación desconocida"
    assert record["imageUrl"] is None
    assert record["results"] == {
        "cloudTypes": [],
        "cloudDetails": [],
        "forecast": "",
        "warnings": [],
    }


def test_update_analysis_results_deduplicates_clouds_forecasts_and_warnings():
    results = {
        "cloudTypes": [],
        "cloudDetails": [],
        "forecast": "",
        "warnings": [],
    }
    row_without_box = SimpleNamespace(
        cloud_type="Cúmulos",
        box_ymin=None,
        box_xmin=None,
        box_ymax=None,
        box_xmax=None,
        forecast="Buen tiempo",
        warning="Sin avisos",
        warning_level=0,
    )
    row_with_box = SimpleNamespace(
        cloud_type="Cúmulos",
        box_ymin=1,
        box_xmin=2,
        box_ymax=3,
        box_xmax=4,
        forecast="Buen tiempo",
        warning="Sin avisos",
        warning_level=0,
    )

    _update_analysis_results(results, row_without_box)
    _update_analysis_results(results, row_with_box)

    assert results["cloudTypes"] == ["cumulus"]
    assert results["cloudDetails"] == [
        {
            "type": "cumulus",
            "originalType": "Cúmulos",
            "box": [1, 2, 3, 4],
        }
    ]
    assert results["forecast"] == "Buen tiempo"
    assert results["warnings"] == [
        {"type": "cumulus", "text": "Sin avisos", "level": 0}
    ]


def test_validate_uploaded_jpeg_rejects_empty_file():
    file = SimpleNamespace(filename="empty.jpg", content_type="image/jpeg")

    with pytest.raises(HTTPException) as exc_info:
        _validate_uploaded_jpeg(file, b"")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "IMAGE_EMPTY"


def test_validate_uploaded_jpeg_rejects_non_jpg_file():
    file = SimpleNamespace(filename="not-a-jpg.txt", content_type="text/plain")

    with pytest.raises(HTTPException) as exc_info:
        _validate_uploaded_jpeg(file, b"not-a-jpeg-image")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "INVALID_IMAGE_FORMAT_JPG_ONLY"


def test_validate_uploaded_jpeg_accepts_jpg_signature_extension_and_content_type():
    file = SimpleNamespace(filename="cloud.jpg", content_type="image/jpeg")

    _validate_uploaded_jpeg(file, b"\xff\xd8\xff\xe0valid-jpeg-like-content")


def test_cancel_get_requires_auth_and_documents_method_not_allowed_response():
    route = next(
        route
        for route in router.routes
        if route.path == "/{analysis_id}/cancel" and "GET" in route.methods
    )

    assert route.responses[405]["description"] == "Method Not Allowed"
    assert route.dependant.dependencies
