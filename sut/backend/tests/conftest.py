import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TEST_MODE", "true")
os.environ.setdefault("DISABLE_WORKER", "true")


@pytest.fixture(autouse=True)
def reset_settings_between_tests():
    from app.infrastructure.config import reset_settings_cache

    reset_settings_cache()
    yield
    reset_settings_cache()
