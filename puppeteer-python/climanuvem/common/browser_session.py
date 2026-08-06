# -*- coding: utf-8 -*-
"""Browser lifecycle and login configuration for the ClimaNuvem system
tests. Mirrors selenium-java's ``BaseLoggedClass``.

Pyppeteer's API is asyncio-only, but every page object method in this suite
is exposed *synchronously* (matching both the Selenium reference and this
suite's unittest.TestCase style): ``BrowserSession`` owns one event loop per
test and every page object routes its awaits through ``BasePage._run()``,
which drives that loop with ``run_until_complete``. A fresh incognito
browser context is created before each test and closed afterward,
preventing any state leakage between tests — the pyppeteer equivalent of
Selenium's ``--incognito`` + fresh ChromeDriver session per test.

Entry points for test methods:
  - ``on_welcome_page()``   — navigates to the frontend root and returns a
    ``WelcomePage``, which waits internally until the page is ready.
  - ``login_as_guest()``    — convenience shortcut that clicks "Continuar
    como invitado" and returns a ``HomePage``.

Set ``CI=true`` for headless Chromium in CI. Override the frontend URL and
accounts file via environment variables (see ``climanuvem.common.config``).
"""
import asyncio
import logging
import unittest

import requests
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page

from climanuvem.common import config
from climanuvem.common.test_accounts import TestAccounts

logger = logging.getLogger(__name__)


class BrowserSession:
    """Owns one event loop, browser, incognito context, and page for a single test."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.browser: Browser = self.loop.run_until_complete(self._launch())
        self.context = self.loop.run_until_complete(self.browser.createIncognitoBrowserContext())
        self.page: Page = self.loop.run_until_complete(self.context.newPage())
        logger.info("Browser started")

    @staticmethod
    async def _launch() -> Browser:
        args = ["--disable-blink-features=AutomationControlled"]
        if config.CI:
            args += ["--no-sandbox", "--disable-dev-shm-usage"]
        launch_kwargs = {
            "headless": config.CI,
            "args": args,
            "handleSIGINT": False,
            "handleSIGTERM": False,
            "handleSIGHUP": False,
        }
        if config.PYPPETEER_EXECUTABLE_PATH:
            launch_kwargs["executablePath"] = config.PYPPETEER_EXECUTABLE_PATH
        return await launch(**launch_kwargs)

    def run(self, coro):
        return self.loop.run_until_complete(coro)

    def close(self):
        self.run(self.context.close())
        self.run(self.browser.close())
        self.loop.close()
        logger.info("Browser closed")


class BrowserTestCase(unittest.TestCase):
    """Base class for the ClimaNuvem browser system tests."""

    frontend_url: str = config.FRONTEND_URL
    test_accounts: TestAccounts = None

    @classmethod
    def setUpClass(cls):
        cls.frontend_url = config.FRONTEND_URL
        try:
            cls.test_accounts = TestAccounts.load(config.ACCOUNTS_FILE)
        except (OSError, KeyError) as exc:
            logger.warning(
                "Could not load system-test accounts from %s (%s). Tests that require accounts will fail only "
                "when they request one.",
                config.ACCOUNTS_FILE,
                exc,
            )
            cls.test_accounts = TestAccounts.empty()
        logger.info("Frontend URL: %s", cls.frontend_url)
        logger.info("System-test accounts file: %s", config.ACCOUNTS_FILE)

    def setUp(self):
        self.session = BrowserSession()

    def tearDown(self):
        self.session.close()

    def on_welcome_page(self):
        # Imported lazily to avoid a module-level import cycle with pages/*.
        from climanuvem.pages.welcome_page import WelcomePage

        self.session.run(self.session.page.goto(self.frontend_url))
        return WelcomePage(self.session)

    def login_as_guest(self):
        return self.on_welcome_page().click_anonymous_login()

    def login_as_profile_user(self):
        account = self.test_accounts.profile_account()
        return self.on_welcome_page().click_login_button().login(account.email, account.password).wait_for_home()

    def delete_firebase_account_if_configured(self, email: str, password: str) -> None:
        api_key = config.FIREBASE_WEB_API_KEY
        if not api_key:
            logger.warning("Skipping Firebase account cleanup for %s because FIREBASE_WEB_API_KEY is not set", email)
            return

        try:
            sign_in = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                json={"email": email, "password": password, "returnSecureToken": True},
                timeout=config.HTTP_TIMEOUT_S,
            )
            sign_in.raise_for_status()
            id_token = sign_in.json()["idToken"]

            delete = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={api_key}",
                json={"idToken": id_token},
                timeout=config.HTTP_TIMEOUT_S,
            )
            delete.raise_for_status()
            logger.info("Deleted Firebase account created during test: %s", email)
        except requests.RequestException as exc:
            logger.warning("Could not delete Firebase account created during test: %s (%s)", email, exc)
