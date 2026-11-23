"""System tests for the real image-analysis flow (worker enabled, Ollama available).

Opt in explicitly with ``REAL_OLLAMA_TESTS=true``; without it every test reports as skipped.
"""
import pytest

from climanuvem.common import ApiClient, config, test_images
from tests.api.assertions import assert_problem

pytestmark = [
    pytest.mark.skipif(
        not config.REAL_OLLAMA_TESTS,
        reason="Real Ollama image-analysis tests are disabled. Set REAL_OLLAMA_TESTS=true to run them.",
    ),
    pytest.mark.usefixtures("empty_history"),
]


def upload_and_wait(api: ApiClient, image: bytes, location: str, explain: bool, filename: str = "image.jpg") -> dict:
    """Uploads a valid JPG, checks the 202 'analyzing' answer and waits for the analysis to complete."""
    upload = api.upload(image, location, filename, include_explainability=explain)
    assert upload.status_code == 202, upload.text
    assert upload.json()["status"] == "analyzing"

    analysis_id = upload.json()["id"]
    analysis = api.wait_for_terminal_status(analysis_id)

    assert analysis["status"] == "completed", f"Analysis {analysis_id} must complete (check the Ollama worker logs)"
    return analysis


def has_normalized_box(cloud_details: list[dict]) -> bool:
    return any(
        isinstance(detail.get("box"), list)
        and len(detail["box"]) == 4
        and all(0.0 <= coordinate <= 1.0 for coordinate in detail["box"])
        for detail in cloud_details
    )


def test_cloudy_jpg_completes_with_cloud_results(api: ApiClient) -> None:
    """BASE - JPG under 5 MB without explainability completes with cloud results."""
    completed = upload_and_wait(api, test_images.cloudy(), "Base Gallery City", explain=False)

    assert completed["results"]["cloudTypes"], "A cloudy JPG must report at least one cloud type"


def test_camera_origin_jpg_completes(api: ApiClient) -> None:
    """2 - Camera-origin JPG is processed like a gallery upload."""
    completed = upload_and_wait(
        api, test_images.cloudy(), "Camera City", explain=False, filename="camera-capture.jpg"
    )

    assert completed["status"] == "completed"


def test_missing_file_is_rejected(api: ApiClient) -> None:
    """3 - Upload with no selected file is rejected with 422."""
    response = api.upload(None, "No File City")

    assert response.status_code == 422, response.text


def test_zero_byte_image_is_rejected(api: ApiClient) -> None:
    """4 - Zero-byte image is rejected with 422 IMAGE_EMPTY."""
    response = api.upload(b"", "Empty Image City", "empty.jpg", include_explainability=False)

    assert_problem(response, 422, "IMAGE_EMPTY")


def test_image_larger_than_five_mb_is_rejected(api: ApiClient) -> None:
    """5 - Image larger than 5 MB is rejected with 413 IMAGE_TOO_LARGE_MAX_5MB."""
    response = api.upload(test_images.too_large(), "Too Large City", "too-large.jpg", include_explainability=False)

    assert_problem(response, 413, "IMAGE_TOO_LARGE_MAX_5MB")


def test_non_jpg_upload_is_rejected(api: ApiClient) -> None:
    """6 - Non-JPG upload is rejected with 415 INVALID_IMAGE_FORMAT_JPG_ONLY."""
    response = api.upload(
        test_images.not_a_jpeg(), "Wrong Format City", "not-a-jpg.txt", "text/plain", include_explainability=False
    )

    assert_problem(response, 415, "INVALID_IMAGE_FORMAT_JPG_ONLY")


def test_explainability_completes_with_normalized_boxes(api: ApiClient) -> None:
    """7 - Explainability with clouds completes with normalized bounding boxes."""
    completed = upload_and_wait(api, test_images.cloudy(), "Explainability City", explain=True)

    assert has_normalized_box(completed["results"]["cloudDetails"]), "At least one normalized box must be persisted"


def test_clear_sky_completes_without_boxes(api: ApiClient) -> None:
    """8 - No-cloud JPG without explainability completes without boxes."""
    results = upload_and_wait(api, test_images.clear_sky(), "Clear Sky City", explain=False)["results"]

    cloud_types = results["cloudTypes"]
    assert not cloud_types or "no_cloud" in cloud_types, "A clear sky must yield no clouds or the no_cloud label"
    assert not has_normalized_box(results["cloudDetails"]), "No boxes without explainability"
