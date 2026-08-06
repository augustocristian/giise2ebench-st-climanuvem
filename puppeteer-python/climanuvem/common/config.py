# -*- coding: utf-8 -*-
"""Environment-driven configuration, equivalent to selenium-java's
``test.properties`` + system-property/env-var overrides, collapsed into a
single environment-variable tier (the standard config mechanism for a
pytest-based suite)."""
import os


def _str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _int(key: str, default: int) -> int:
    return int(os.environ.get(key, str(default)))


def _bool(key: str, default: bool) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() == "true"


SUT_URL = _str("SUT_URL", "http://localhost:8000")
FRONTEND_URL = _str("FRONTEND_URL", "http://localhost:5173")
TEST_TOKEN = _str("TEST_TOKEN", "test-token-climanuvem")
HTTP_TIMEOUT_S = _int("HTTP_TIMEOUT_MS", 10_000) / 1000
ANALYSIS_TIMEOUT_MS = _int("ANALYSIS_TIMEOUT_MS", 360_000)
ACCOUNTS_FILE = _str("ACCOUNTS_FILE", "tests/resources/accounts.local.csv")
REGISTER_EMAIL_DOMAIN = _str("REGISTER_EMAIL_DOMAIN", "gmail.com")
FIREBASE_WEB_API_KEY = _str("FIREBASE_WEB_API_KEY", "")
REAL_OLLAMA_TESTS = _bool("REAL_OLLAMA_TESTS", False)
CI = _bool("CI", False)

# pyppeteer's bundled Chromium revision is occasionally pulled from Google's
# snapshot bucket before pyppeteer itself is updated to point elsewhere. If
# `launch()` fails with "Chromium downloadable not found", set this to a
# local Chrome/Chromium executable (e.g. the one installed for regular
# browsing) instead of waiting on a pyppeteer release.
PYPPETEER_EXECUTABLE_PATH = _str("PYPPETEER_EXECUTABLE_PATH", "")
