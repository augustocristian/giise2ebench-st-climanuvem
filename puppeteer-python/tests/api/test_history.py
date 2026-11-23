"""GET /api/v1/analyses (list, pagination, X-Total-Count) and GET /api/v1/analyses/{id}.

Every test starts from an empty history.
"""
import pytest

from climanuvem.common import ApiClient
from climanuvem.common.api_client import NON_EXISTENT_ID
from tests.api.assertions import assert_problem

pytestmark = pytest.mark.usefixtures("empty_history")

ENTRY_FIELDS = {"id", "status", "date", "location", "imageUrl", "results"}
RESULT_FIELDS = {"cloudTypes", "cloudDetails", "forecast", "warnings"}


def test_history_initially_empty(api: ApiClient) -> None:
    response = api.get(api.analyses_url())

    assert response.status_code == 200
    assert response.json() == []


def test_history_entry_has_required_fields(api: ApiClient) -> None:
    analysis_id = api.create_analysis("Oviedo, Spain")

    history = api.list_analyses()

    assert analysis_id in [entry["id"] for entry in history]
    assert ENTRY_FIELDS <= history[0].keys()
    assert RESULT_FIELDS <= history[0]["results"].keys()


def test_get_single_returns_analysis(api: ApiClient) -> None:
    analysis_id = api.create_analysis("Single Get City")

    response = api.get(api.analysis_url(analysis_id))

    analysis = response.json()
    assert response.status_code == 200
    assert analysis["id"] == analysis_id
    assert analysis["status"] == "analyzing"
    assert analysis["location"] == "Single Get City"
    assert analysis["imageUrl"] == f"/api/v1/analyses/{analysis_id}/image"
    assert "results" in analysis
    assert analysis["date"].endswith("Z"), "ISO-8601 UTC timestamp"


def test_get_single_unknown_returns_404(api: ApiClient) -> None:
    assert_problem(api.get(api.analysis_url(NON_EXISTENT_ID)), 404, "ANALYSIS_NOT_FOUND")


def test_pagination_returns_newest_first_and_total_count(api: ApiClient) -> None:
    first, second, third = (api.create_analysis(f"Page City {n}") for n in (1, 2, 3))

    page0 = api.get(api.analyses_url("?page=0&size=2"))
    page1 = api.get(api.analyses_url("?page=1&size=2"))

    assert page0.headers["X-Total-Count"] == "3"
    assert [entry["id"] for entry in page0.json()] == [third, second], "First page, newest first"
    assert [entry["id"] for entry in page1.json()] == [first], "Second page holds the remainder"


@pytest.mark.parametrize("query", ["?size=0", "?size=101", "?page=-1"])
def test_out_of_range_pagination_returns_422(api: ApiClient, query: str) -> None:
    assert api.get(api.analyses_url(query)).status_code == 422
