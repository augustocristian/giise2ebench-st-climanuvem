"""Authenticated image delivery (GET /api/v1/analyses/{id}/image) and the removed public /uploads mount."""
import time

from climanuvem.common import ApiClient
from climanuvem.common.api_client import NON_EXISTENT_ID
from tests.api.assertions import assert_problem

JPEG_MAGIC = b"\xff\xd8\xff"


def test_owner_gets_jpeg(api: ApiClient) -> None:
    analysis_id = api.create_analysis(f"Image City {time.time_ns()}")

    response = api.get(api.image_url(analysis_id))

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/jpeg")
    assert response.content.startswith(JPEG_MAGIC), "JPEG magic bytes"


def test_image_requires_authorization(api: ApiClient) -> None:
    analysis_id = api.create_analysis("Image Auth City")

    assert_problem(api.get(api.image_url(analysis_id), auth=False), 401, "NOT_AUTHENTICATED")


def test_image_unknown_id_returns_404(api: ApiClient) -> None:
    assert_problem(api.get(api.image_url(NON_EXISTENT_ID)), 404, "ANALYSIS_NOT_FOUND")


def test_uploads_mount_is_gone(api: ApiClient) -> None:
    assert api.get("/uploads/anything.jpg", auth=False).status_code == 404
