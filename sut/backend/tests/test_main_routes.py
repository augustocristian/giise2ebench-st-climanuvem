import importlib
from fastapi.testclient import TestClient
from app.infrastructure.config import reset_settings_cache


def _load_main_with_test_mode(monkeypatch, enabled: bool):
    monkeypatch.setenv("TEST_MODE", "true" if enabled else "false")
    reset_settings_cache()

    import app.main as main_module

    return importlib.reload(main_module)


def test_test_route_is_only_registered_in_test_mode(monkeypatch):
    main_module = _load_main_with_test_mode(monkeypatch, True)
    assert TestClient(main_module.app).get("/test").status_code != 404

    main_module = _load_main_with_test_mode(monkeypatch, False)
    assert TestClient(main_module.app).get("/test").status_code == 404

    _load_main_with_test_mode(monkeypatch, True)
