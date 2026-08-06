# -*- coding: utf-8 -*-
"""Browser system tests for the login functionality, derived from the same
Base Choice table as selenium-java's ``TestLoginSystem``.

Each Java ``Assertions.assertAll(...)`` bundle becomes a ``self.subTest(...)``
block here — Python's built-in equivalent: a subTest failure is recorded and
the test continues, so every sub-check still runs and is reported
individually instead of stopping at the first failure.
"""
import logging
import unittest

from climanuvem.common.browser_session import BrowserTestCase

logger = logging.getLogger(__name__)


class TestLoginSystem(BrowserTestCase):

    def test_guest_login_reaches_home(self):
        """BASE - Guest login reaches Home"""
        logger.debug("Starting the test: " + self._testMethodName)
        home = self.login_as_guest()
        assert home.is_welcome_message_visible(), "Guest login must reach the Home screen"
        logger.debug("Ending the test: " + self._testMethodName)

    def test_google_login_provider_flow_is_available(self):
        """BASE - Google login provider flow is available"""
        logger.debug("Starting the test: " + self._testMethodName)
        login = self.on_welcome_page().click_login_button()

        with self.subTest("Google login option must be available"):
            assert login.is_google_login_present()
        with self.subTest("Clicking Google login must start the provider flow"):
            assert login.click_google_login_starts_provider()
        logger.debug("Ending the test: " + self._testMethodName)

    def test_existing_email_with_correct_password_reaches_home(self):
        """2 - Existing email with correct password reaches Home"""
        logger.debug("Starting the test: " + self._testMethodName)
        for account in self.test_accounts.login_accounts():
            with self.subTest(account=str(account)):
                home = (
                    self.on_welcome_page()
                    .click_login_button()
                    .login(account.email, account.password)
                    .wait_for_home()
                )
                assert home.is_welcome_message_visible(), (
                    "Existing email with correct password must reach the Home screen"
                )
                home.click_logout()  # leave a clean Welcome screen for the next account/test
        logger.debug("Ending the test: " + self._testMethodName)

    def test_invalid_email_password_login_attempts_are_rejected(self):
        """3 - Invalid email/password login attempts are rejected"""
        logger.debug("Starting the test: " + self._testMethodName)
        unknown = self.test_accounts.unknown_account()

        for account in self.test_accounts.login_accounts():
            login = self.on_welcome_page().click_login_button()

            with self.subTest(account=str(account), case="existing email, empty password"):
                self._assert_login_rejected(login, account.email, "")
            with self.subTest(account=str(account), case="unknown email, some password"):
                self._assert_login_rejected(login, unknown.email, unknown.password)
            with self.subTest(account=str(account), case="empty credentials"):
                self._assert_login_rejected(login, "", "")
            with self.subTest(account=str(account), case="existing email, incorrect password"):
                self._assert_login_rejected(login, account.email, unknown.password)
        logger.debug("Ending the test: " + self._testMethodName)

    def _assert_login_rejected(self, login_page, email, password):
        login_page.login(email, password)
        try:
            assert login_page.wait_for_login_failure().has_login_error_or_validation()
        finally:
            login_page.close_login_feedback_if_present()


if __name__ == '__main__':
    unittest.main()
