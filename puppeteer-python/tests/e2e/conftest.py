"""Fixtures shared by the browser tests: test accounts, screens already opened, Firebase cleanup."""
import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
import requests

from climanuvem.browser import Page
from climanuvem.common import TestAccount, TestAccounts, config
from climanuvem.pages import HomePage, LoginPage, RegisterPage, WelcomePage

logger = logging.getLogger(__name__)

IDENTITY_TOOLKIT_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
MISSING_LOGIN_ACCOUNTS = pytest.param(None, id="no-login-accounts")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Runs every test that asks for ``login_account`` once per ``login_user`` row of the accounts file."""
    if "login_account" not in metafunc.fixturenames:
        return
    try:
        params = [pytest.param(account, id=account.email) for account in TestAccounts.load().login_accounts()]
    except (AssertionError, FileNotFoundError):  # no accounts configured: fail the tests, not the collection
        params = [MISSING_LOGIN_ACCOUNTS]
    metafunc.parametrize("login_account", params, indirect=True)


@pytest.fixture
def login_account(request: pytest.FixtureRequest) -> TestAccount:
    """One existing, verified account (parametrized by ``pytest_generate_tests``)."""
    if request.param is None:
        pytest.fail("Configure at least one login_user in ACCOUNTS_FILE (see tests/resources/accounts.template.csv).")
    return request.param


@pytest.fixture(scope="session")
def accounts() -> TestAccounts:
    return TestAccounts.load()


@pytest_asyncio.fixture(loop_scope="session")
async def welcome_page(page: Page, frontend_url: str) -> WelcomePage:
    """The Welcome screen of a fresh session."""
    await page.goto(frontend_url)
    return await WelcomePage.create(page)


@pytest_asyncio.fixture(loop_scope="session")
async def login_page(welcome_page: WelcomePage) -> LoginPage:
    return await welcome_page.click_login_button()


@pytest_asyncio.fixture(loop_scope="session")
async def register_page(login_page: LoginPage) -> RegisterPage:
    return await login_page.open_register()


@pytest_asyncio.fixture(loop_scope="session")
async def home_page(welcome_page: WelcomePage) -> HomePage:
    """Home after continuing as guest."""
    return await welcome_page.click_anonymous_login()


@pytest_asyncio.fixture(loop_scope="session")
async def profile_home_page(login_page: LoginPage, accounts: TestAccounts) -> HomePage:
    """Home after logging in with the profile account."""
    account = accounts.profile_account()
    return await login_page.login(account.email, account.password)


@pytest.fixture
def unique_email() -> Callable[[], str]:
    """Factory of never-used addresses on the configured registration domain."""
    return lambda: f"climanuvem.test+{int(time.time() * 1000)}{uuid.uuid4().hex[:6]}@{config.REGISTER_EMAIL_DOMAIN}"


def _delete_firebase_account(email: str, password: str) -> None:
    """Best-effort deletion of an account created during a test; needs FIREBASE_WEB_API_KEY."""
    if not config.FIREBASE_WEB_API_KEY:
        logger.info("Skipping Firebase account cleanup for %s: FIREBASE_WEB_API_KEY not configured", email)
        return
    params = {"key": config.FIREBASE_WEB_API_KEY}
    try:
        sign_in = requests.post(
            f"{IDENTITY_TOOLKIT_URL}:signInWithPassword", params=params, timeout=config.HTTP_TIMEOUT_S,
            json={"email": email, "password": password, "returnSecureToken": True})
        sign_in.raise_for_status()
        delete = requests.post(
            f"{IDENTITY_TOOLKIT_URL}:delete", params=params, timeout=config.HTTP_TIMEOUT_S,
            json={"idToken": sign_in.json()["idToken"]})
        delete.raise_for_status()
        logger.info("Deleted Firebase account created during the test: %s", email)
    except requests.RequestException as error:
        logger.warning("Could not delete Firebase account created during the test: %s (%s)", email, error)


@pytest_asyncio.fixture(loop_scope="session")
async def created_accounts() -> AsyncIterator[list[tuple[str, str]]]:
    """Tests append the ``(email, password)`` of every account they really create; they are deleted afterwards."""
    created: list[tuple[str, str]] = []
    yield created
    for email, password in created:
        await asyncio.to_thread(_delete_firebase_account, email, password)
