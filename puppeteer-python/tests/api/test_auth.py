"""Authentication enforcement: a missing Authorization header yields 401 NOT_AUTHENTICATED with a Bearer challenge.

In TEST_MODE any token is accepted, so an invalid token is not exercised.
"""
import pytest

from climanuvem.common import ApiClient, test_images
from tests.api.assertions import assert_unauthenticated


def test_test_endpoint_with_token_returns_user(api: ApiClient) -> None:
    response = api.get(api.api_url("/test"))

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Test successful"
    assert "user" in body


@pytest.mark.parametrize("method, path", [
    ("GET", "/test"),
    ("GET", "/analyses"),
    ("GET", "/analyses/1"),
    ("GET", "/analyses/1/image"),
    ("DELETE", "/analyses/1"),
    ("DELETE", "/analyses"),
])
def test_protected_endpoint_requires_authorization(api: ApiClient, method: str, path: str) -> None:
    assert_unauthenticated(api.send(method, api.api_url(path), auth=False))


def test_patch_requires_authorization(api: ApiClient) -> None:
    assert_unauthenticated(api.patch_status(api.analysis_url(1), "cancelled", auth=False))


def test_upload_requires_authorization(api: ApiClient) -> None:
    assert_unauthenticated(api.upload(test_images.tiny(), "No Auth City", auth=False))
