"""PATCH /api/v1/analyses/{id} with {"status": "cancelled"}.

Runs with DISABLE_WORKER=true so analyses stay 'analyzing', which makes cancellation deterministic without Ollama.
"""
from climanuvem.common import ApiClient
from climanuvem.common.api_client import NON_EXISTENT_ID
from tests.api.assertions import assert_problem


def test_cancel_returns_updated_analysis(api: ApiClient) -> None:
    analysis_id = api.create_analysis("Cancel Me City")

    response = api.patch_status(api.analysis_url(analysis_id), "cancelled")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == analysis_id
    assert response.json()["status"] == "cancelled"


def test_cancel_twice_returns_409(api: ApiClient) -> None:
    url = api.analysis_url(api.create_analysis("Double Cancel City"))
    api.patch_status(url, "cancelled")

    assert_problem(api.patch_status(url, "cancelled"), 409, "ANALYSIS_NOT_CANCELLABLE")


def test_cancel_unknown_returns_404(api: ApiClient) -> None:
    assert_problem(api.patch_status(api.analysis_url(NON_EXISTENT_ID), "cancelled"), 404, "ANALYSIS_NOT_FOUND")


def test_patch_with_other_status_returns_422_and_leaves_analysis_untouched(api: ApiClient) -> None:
    url = api.analysis_url(api.create_analysis("Bad Status City"))

    response = api.patch_status(url, "completed")

    assert response.status_code == 422
    assert api.get(url).json()["status"] == "analyzing"
