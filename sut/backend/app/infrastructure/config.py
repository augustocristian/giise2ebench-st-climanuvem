import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://localhost:8081,"
    "http://localhost:19006,"
    "http://127.0.0.1:8081,"
    "http://127.0.0.1:19006"
)


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() == "true"


def _cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", DEFAULT_CORS_ALLOW_ORIGINS).split(",")
        if origin.strip()
    ]


@dataclass(frozen=True)
class Settings:
    firebase_key_path: str | None
    firebase_clock_skew_seconds: int
    database_url: str | None
    ollama_url: str | None
    ollama_model: str
    log_level: str
    test_mode: bool
    test_token: str
    test_user_uid: str
    disable_worker: bool
    cors_allow_origins: list[str]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        firebase_key_path=os.getenv("FIREBASE_KEY_PATH"),
        firebase_clock_skew_seconds=int(os.getenv("FIREBASE_CLOCK_SKEW_SECONDS", "5")),
        database_url=os.getenv("DATABASE_URL"),
        ollama_url=os.getenv("OLLAMA_URL"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        test_mode=_env_bool("TEST_MODE"),
        test_token=os.getenv("TEST_TOKEN", "test-token-climanuvem"),
        test_user_uid=os.getenv("TEST_USER_UID", "test-user-e2e"),
        disable_worker=_env_bool("DISABLE_WORKER"),
        cors_allow_origins=_cors_origins(),
    )


def reset_settings_cache():
    get_settings.cache_clear()
