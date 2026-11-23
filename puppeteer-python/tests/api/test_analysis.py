"""POST /api/v1/analyses (202 Accepted + Location + {id, status}) and 405 handling.

Runs with DISABLE_WORKER=true, so uploads stay in 'analyzing' and no Ollama is needed.
"""
import time

from climanuvem.common import ApiClient, test_images
from tests.api.assertions import assert_method_not_allowed


def test_upload_returns_accepted_with_location(api: ApiClient) -> None:
    response = api.upload(test_images.tiny())

    body = response.json()
    assert response.status_code == 202
    assert body["id"] > 0
    assert body["status"] == "analyzing"
    assert "analysis_id" not in body, "Legacy 'analysis_id' must be gone"
    assert response.headers["Location"].endswith(f"/api/v1/analyses/{body['id']}")


def test_upload_stores_location(api: ApiClient) -> None:
    location = f"Madrid, Spain {time.time_ns()}"
    analysis_id = api.create_analysis(location)

    analysis = api.get(api.analysis_url(analysis_id)).json()

    assert analysis["location"] == location


def test_upload_accepts_optional_fields(api: ApiClient) -> None:
    optional = {"fcmToken": "test-fcm-token", "latitude": "43.5322", "longitude": "-5.6611"}

    response = api.upload(test_images.tiny(), "Gijon", include_explainability=True, extra_fields=optional)

    assert response.status_code == 202, response.text


def test_consecutive_uploads_have_distinct_ids(api: ApiClient) -> None:
    assert api.create_analysis("Location A") != api.create_analysis("Location B")


def test_unsupported_method_on_collection_returns_405(api: ApiClient) -> None:
    assert_method_not_allowed(api.send("PUT", api.analyses_url()), "GET", "POST", "DELETE")


def test_post_on_single_analysis_returns_405(api: ApiClient) -> None:
    analysis_id = api.create_analysis("Method Check City")

    assert_method_not_allowed(api.send("POST", api.analysis_url(analysis_id)), "GET", "PATCH", "DELETE")
