import importlib
from app.infrastructure.config import reset_settings_cache


def _load_main_with_test_mode(monkeypatch, enabled: bool):
    monkeypatch.setenv("TEST_MODE", "true" if enabled else "false")
    reset_settings_cache()

    import app.main as main_module

    return importlib.reload(main_module)


def test_test_route_is_only_registered_in_test_mode(monkeypatch):
    main_module = _load_main_with_test_mode(monkeypatch, True)
    assert any(route.path == "/test" for route in main_module.app.routes)

    main_module = _load_main_with_test_mode(monkeypatch, False)
    assert not any(route.path == "/test" for route in main_module.app.routes)

    _load_main_with_test_mode(monkeypatch, True)
