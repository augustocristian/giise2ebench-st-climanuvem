"""DELETE /api/v1/analyses/{id} and DELETE /api/v1/analyses (both 204 with an empty body)."""
from climanuvem.common import ApiClient
from climanuvem.common.api_client import NON_EXISTENT_ID
from tests.api.assertions import assert_problem


def test_delete_single_returns_204_and_analysis_disappears(api: ApiClient) -> None:
    analysis_id = api.create_analysis("Delete Me City")

    response = api.delete(api.analysis_url(analysis_id))

    assert response.status_code == 204
    assert response.content == b""
    assert analysis_id not in [entry["id"] for entry in api.list_analyses()], "Deleted analysis must not be listed"
    assert api.get(api.analysis_url(analysis_id)).status_code == 404


def test_delete_unknown_returns_404(api: ApiClient) -> None:
    assert_problem(api.delete(api.analysis_url(NON_EXISTENT_ID)), 404, "ANALYSIS_NOT_FOUND")


def test_delete_collection_clears_history(api: ApiClient) -> None:
    api.create_analysis("Bulk Delete A")
    api.create_analysis("Bulk Delete B")

    response = api.delete(api.analyses_url())

    assert response.status_code == 204
    assert response.content == b""
    assert api.list_analyses() == []


def test_delete_collection_when_empty_returns_204(api: ApiClient) -> None:
    api.delete_all_analyses()

    assert api.delete(api.analyses_url()).status_code == 204
