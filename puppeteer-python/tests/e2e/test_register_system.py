# -*- coding: utf-8 -*-
"""Browser system tests for account creation, derived from the same Base
Choice table as selenium-java's ``TestRegisterSystem``.
"""
import logging
import time
import unittest

from climanuvem.common import config
from climanuvem.common.browser_session import BrowserTestCase

logger = logging.getLogger(__name__)

VALID_USERNAME_20 = "usuarioPrueba1234567"
USERNAME_2 = "ab"
USERNAME_21 = "usuarioPrueba12345678"
VALID_PASSWORD = "Test12"
PASSWORD_5 = "Test1"
PASSWORD_NO_UPPERCASE = "test12"
PASSWORD_NO_NUMBER = "Testaa"
DIFFERENT_CONFIRM_PASSWORD = "Other1"


def _unique_register_email() -> str:
    return f"climanuvem.test+{int(time.time() * 1000)}@{config.REGISTER_EMAIL_DOMAIN}"


class TestRegisterSystem(BrowserTestCase):

    def test_valid_account_data_creates_account(self):
        """BASE - Valid account data creates the account"""
        logger.debug("Starting the test: " + self._testMethodName)
        email = _unique_register_email()

        try:
            register_page = (
                self._open_register_page()
                .register(VALID_USERNAME_20, email, VALID_PASSWORD, VALID_PASSWORD)
                .wait_for_verification_dialog()
            )
            assert register_page.is_verification_dialog_visible(), (
                "Valid registration data must create the account and show email-verification guidance"
            )
        finally:
            self.delete_firebase_account_if_configured(email, VALID_PASSWORD)
        logger.debug("Ending the test: " + self._testMethodName)

    def test_username_and_email_validation_errors_are_rejected(self):
        """2 - Username and email validation errors are rejected"""
        logger.debug("Starting the test: " + self._testMethodName)
        existing_account = self.test_accounts.login_account()

        with self.subTest("Empty username must be rejected"):
            self._assert_registration_rejected("", _unique_register_email(), VALID_PASSWORD, VALID_PASSWORD)
        with self.subTest("Two-character username must be rejected"):
            self._assert_registration_rejected(USERNAME_2, _unique_register_email(), VALID_PASSWORD, VALID_PASSWORD)
        with self.subTest("Twenty-one-character username must be rejected"):
            self._assert_registration_rejected(USERNAME_21, _unique_register_email(), VALID_PASSWORD, VALID_PASSWORD)
        with self.subTest("Invalid email must be rejected"):
            self._assert_registration_rejected(VALID_USERNAME_20, "correo-invalido", VALID_PASSWORD, VALID_PASSWORD)
        with self.subTest("Email already in use must be rejected"):
            self._assert_registration_rejected(
                VALID_USERNAME_20, existing_account.email, VALID_PASSWORD, VALID_PASSWORD
            )
        logger.debug("Ending the test: " + self._testMethodName)

    def test_password_and_confirmation_validation_errors_are_rejected(self):
        """3 - Password and confirmation validation errors are rejected"""
        logger.debug("Starting the test: " + self._testMethodName)

        with self.subTest("Empty password must be rejected"):
            self._assert_registration_rejected(VALID_USERNAME_20, _unique_register_email(), "", "")
        with self.subTest("Five-character password must be rejected"):
            self._assert_registration_rejected(VALID_USERNAME_20, _unique_register_email(), PASSWORD_5, PASSWORD_5)
        with self.subTest("Password without uppercase letters must be rejected"):
            self._assert_registration_rejected(
                VALID_USERNAME_20, _unique_register_email(), PASSWORD_NO_UPPERCASE, PASSWORD_NO_UPPERCASE
            )
        with self.subTest("Password without numbers must be rejected"):
            self._assert_registration_rejected(
                VALID_USERNAME_20, _unique_register_email(), PASSWORD_NO_NUMBER, PASSWORD_NO_NUMBER
            )
        with self.subTest("Non-matching password confirmation must be rejected"):
            self._assert_registration_rejected(
                VALID_USERNAME_20, _unique_register_email(), VALID_PASSWORD, DIFFERENT_CONFIRM_PASSWORD
            )
        logger.debug("Ending the test: " + self._testMethodName)

    def _open_register_page(self):
        return self.on_welcome_page().click_login_button().click_register_link()

    def _assert_registration_rejected(self, username, email, password, confirm_password):
        register_page = self._open_register_page().register(username, email, password, confirm_password)
        assert register_page.wait_for_register_failure().has_register_error_or_validation()


if __name__ == '__main__':
    unittest.main()
