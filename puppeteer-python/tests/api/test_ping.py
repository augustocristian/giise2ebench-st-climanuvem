"""Public health-check endpoints (no authentication) and the removed legacy routes."""
import pytest

from climanuvem.common import ApiClient


def test_ping_returns_pong(api: ApiClient) -> None:
    response = api.get(api.api_url("/ping"), auth=False)

    assert response.status_code == 200
    assert response.json()["ping"] == "pong"


@pytest.mark.parametrize("path", ["/", ""], ids=["with_trailing_slash", "without_trailing_slash"])
def test_root_returns_service_status(api: ApiClient, path: str) -> None:
    response = api.get(api.api_url(path), auth=False)

    assert response.status_code == 200
    assert response.json() == {"service": "ClimaNuvem API", "status": "ok"}


def test_legacy_ping_returns_404(api: ApiClient) -> None:
    assert api.get("/ping", auth=False).status_code == 404
