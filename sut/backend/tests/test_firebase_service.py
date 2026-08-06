import importlib
from app.infrastructure.config import reset_settings_cache


def test_verify_token_uses_configured_clock_skew(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "false")
    monkeypatch.setenv("FIREBASE_KEY_PATH", "secrets/firebase_key.json")
    monkeypatch.setenv("FIREBASE_CLOCK_SKEW_SECONDS", "5")
    reset_settings_cache()

    import firebase_admin
    import app.infrastructure.firebase_service as firebase_service

    monkeypatch.setattr(firebase_admin.credentials, "Certificate", lambda path: object())
    monkeypatch.setattr(firebase_admin, "initialize_app", lambda credential: None)
    firebase_service = importlib.reload(firebase_service)

    expected_decoded_token = {"uid": "test-user"}
    verify_id_token_calls = []

    def verify_id_token(token, clock_skew_seconds):
        verify_id_token_calls.append((token, clock_skew_seconds))
        return expected_decoded_token

    monkeypatch.setattr(firebase_service.auth, "verify_id_token", verify_id_token)

    decoded_token = firebase_service.verify_token("firebase-token")

    assert decoded_token == expected_decoded_token
    assert verify_id_token_calls == [("firebase-token", 5)]
