import pytest
from app.infrastructure.config import reset_settings_cache


def test_authenticate_user_in_test_mode_uses_custom_provider(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEST_TOKEN", "known-token")
    monkeypatch.setenv("TEST_USER_UID", "test-user")
    reset_settings_cache()

    import app.business.auth_service as auth_service

    user = auth_service.authenticate_user("known-token")

    assert user["uid"] == "test-user"
    assert user["firebase"]["sign_in_provider"] == "custom"


def test_authenticate_user_in_test_mode_marks_other_tokens_anonymous(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEST_TOKEN", "known-token")
    monkeypatch.setenv("TEST_USER_UID", "test-user")
    reset_settings_cache()

    import app.business.auth_service as auth_service

    user = auth_service.authenticate_user("anonymous-token")

    assert user["uid"] == "test-user"
    assert user["firebase"]["sign_in_provider"] == "anonymous"


def test_authenticate_user_raises_when_firebase_rejects_token(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "false")
    reset_settings_cache()

    import app.business.auth_service as auth_service

    monkeypatch.setattr(auth_service, "verify_token", lambda token: None)

    with pytest.raises(auth_service.InvalidTokenError, match="Invalid token"):
        auth_service.authenticate_user("bad-token")
