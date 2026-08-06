import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.presentation.dependencies import auth_dependency


def test_get_current_user_rejects_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        auth_dependency.get_current_user(None)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authenticated"


def test_get_current_user_returns_authenticated_user(monkeypatch):
    expected_user = {"uid": "user-1"}
    monkeypatch.setattr(auth_dependency, "authenticate_user", lambda token: expected_user)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    assert auth_dependency.get_current_user(credentials) == expected_user


def test_get_current_user_maps_invalid_tokens(monkeypatch):
    def reject_token(_token):
        raise auth_dependency.InvalidTokenError("bad token")

    monkeypatch.setattr(auth_dependency, "authenticate_user", reject_token)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")

    with pytest.raises(HTTPException) as exc_info:
        auth_dependency.get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
