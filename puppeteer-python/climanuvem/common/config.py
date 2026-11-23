"""Environment-driven configuration of the ClimaNuvem test suite.

Everything is read from environment variables once, at import time.
"""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _flag(key: str) -> bool:
    return os.environ.get(key, "").strip().lower() in ("1", "true", "yes")


SUT_URL = os.environ.get("SUT_URL", "http://localhost:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
TEST_TOKEN = os.environ.get("TEST_TOKEN", "test-token-climanuvem")
HTTP_TIMEOUT_S = int(os.environ.get("HTTP_TIMEOUT_MS", "10000")) / 1000
ANALYSIS_TIMEOUT_S = int(os.environ.get("ANALYSIS_TIMEOUT_MS", "360000")) / 1000
ACCOUNTS_FILE = Path(os.environ.get("ACCOUNTS_FILE") or ROOT_DIR / "tests" / "resources" / "accounts.local.csv")
REGISTER_EMAIL_DOMAIN = os.environ.get("REGISTER_EMAIL_DOMAIN", "gmail.com")
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY", "")
REAL_OLLAMA_TESTS = _flag("REAL_OLLAMA_TESTS")
PASSWORD_POLICY_ENFORCED = _flag("PASSWORD_POLICY_ENFORCED")

# Browser: headless unless HEADED=1; the bridge uses the system Chrome unless PUPPETEER_EXECUTABLE_PATH is set.
HEADED = _flag("HEADED")
BROWSER_EXECUTABLE_PATH = os.environ.get("PUPPETEER_EXECUTABLE_PATH") or None
BROWSER_ARGS = os.environ.get("BROWSER_ARGS", "").split()
