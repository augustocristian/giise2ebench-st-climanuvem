"""Browser system tests for account creation, derived from the Base Choice table of
selenium-java's ``TestRegisterSystem``."""
import re
from collections.abc import Callable

import pytest

from climanuvem.common import TestAccounts, config
from climanuvem.pages import RegisterPage

VALID_USERNAME_20 = "TestUser123456789012"
USERNAME_2 = "ab"
USERNAME_21 = "TestUser1234567890123"
VALID_PASSWORD = "Test12"
PASSWORD_5 = "Test1"
PASSWORD_NO_UPPERCASE = "test12"
PASSWORD_NO_NUMBER = "Testaa"
DIFFERENT_CONFIRM_PASSWORD = "Other1"

ERROR_TITLE = "Error"
USERNAME_LENGTH_MESSAGE = "Username must be between 3 and 20 characters."
INVALID_EMAIL_MESSAGE = "Please enter a valid email address."
PASSWORD_LENGTH_MESSAGE = "Password must be at least 6 characters."
PASSWORDS_DO_NOT_MATCH_MESSAGE = "Passwords do not match."
EMAIL_IN_USE_MESSAGE = "This email is already in use by another account."
WEAK_PASSWORD_MESSAGE = re.compile("uppercase letter and one number|too weak")


async def assert_registration_rejected(
    register: RegisterPage, username: str, email: str, password: str, confirm_password: str,
    message: str | re.Pattern[str],
) -> None:
    """Submits the form, expects the error dialog and closes it so the form can be reused."""
    await register.register(username, email, password, confirm_password)
    await register.expect_feedback(ERROR_TITLE, message)
    await register.dismiss_feedback()


async def test_valid_account_data_creates_account(
    register_page: RegisterPage, created_accounts: list[tuple[str, str]], unique_email: Callable[[], str]
) -> None:
    """BASE - Valid account data creates the account"""
    email = unique_email()
    created_accounts.append((email, VALID_PASSWORD))

    await register_page.register(VALID_USERNAME_20, email, VALID_PASSWORD, VALID_PASSWORD)

    await register_page.expect_feedback("Successful registration", "verification email")


async def test_username_and_email_validation_errors_are_rejected(
    register_page: RegisterPage, accounts: TestAccounts, unique_email: Callable[[], str]
) -> None:
    """2 - Username and email validation errors are rejected"""
    existing = accounts.login_account()

    await assert_registration_rejected(
        register_page, "", unique_email(), VALID_PASSWORD, VALID_PASSWORD, USERNAME_LENGTH_MESSAGE)
    await assert_registration_rejected(
        register_page, USERNAME_2, unique_email(), VALID_PASSWORD, VALID_PASSWORD, USERNAME_LENGTH_MESSAGE)
    await assert_registration_rejected(
        register_page, VALID_USERNAME_20, "invalid-email", VALID_PASSWORD, VALID_PASSWORD, INVALID_EMAIL_MESSAGE)
    await assert_registration_rejected(
        register_page, VALID_USERNAME_20, existing.email, VALID_PASSWORD, VALID_PASSWORD, EMAIL_IN_USE_MESSAGE)


async def test_password_and_confirmation_validation_errors_are_rejected(
    register_page: RegisterPage, unique_email: Callable[[], str]
) -> None:
    """3 - Password and confirmation validation errors are rejected"""
    await assert_registration_rejected(
        register_page, VALID_USERNAME_20, unique_email(), "", "", PASSWORD_LENGTH_MESSAGE)
    await assert_registration_rejected(
        register_page, VALID_USERNAME_20, unique_email(), PASSWORD_5, PASSWORD_5, PASSWORD_LENGTH_MESSAGE)
    await assert_registration_rejected(
        register_page, VALID_USERNAME_20, unique_email(), VALID_PASSWORD, DIFFERENT_CONFIRM_PASSWORD,
        PASSWORDS_DO_NOT_MATCH_MESSAGE)


async def test_username_field_caps_length_at_twenty_characters(register_page: RegisterPage) -> None:
    """2b - The username field caps its value at 20 characters"""
    assert await register_page.type_username(USERNAME_21) == VALID_USERNAME_20


@pytest.mark.skipif(
    not config.PASSWORD_POLICY_ENFORCED,
    reason="The Firebase Auth emulator does not enforce password policies; "
           "set PASSWORD_POLICY_ENFORCED=true against a real project.",
)
async def test_password_policy_violations_are_rejected(
    register_page: RegisterPage, unique_email: Callable[[], str]
) -> None:
    """3b - Passwords without an uppercase letter or a number are rejected"""
    for weak_password in (PASSWORD_NO_UPPERCASE, PASSWORD_NO_NUMBER):
        await assert_registration_rejected(
            register_page, VALID_USERNAME_20, unique_email(), weak_password, weak_password,
            WEAK_PASSWORD_MESSAGE)
