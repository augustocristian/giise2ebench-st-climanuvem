"""Browser system tests for the login functionality, derived from the Base Choice table of
selenium-java's ``TestLoginSystem``. Existing-account scenarios run once per ``login_user`` account."""
import re

from climanuvem.common import TestAccount, TestAccounts
from climanuvem.pages import HomePage, LoginPage

ERROR_TITLE = "Error"
INVALID_EMAIL_MESSAGE = "Please enter a valid email address."
# Real Firebase answers with a generic message; the emulator is more specific (wrong password / unknown email).
BAD_CREDENTIALS_MESSAGE = re.compile(
    "Incorrect credentials|password is incorrect|No account exists|Authentication error")


async def assert_login_rejected(login: LoginPage, email: str, password: str, message: str | re.Pattern[str]) -> None:
    await login.submit_credentials(email, password)
    await login.expect_feedback(ERROR_TITLE, message)
    await login.dismiss_feedback()


async def test_guest_login_reaches_home(home_page: HomePage) -> None:
    """BASE - Guest login reaches Home"""
    assert await home_page.is_welcome_message_visible()


async def test_google_login_provider_flow_is_available(login_page: LoginPage) -> None:
    """BASE - Google login provider flow is available"""
    assert await login_page.is_google_login_visible()
    assert await login_page.start_google_login(), "Clicking Google login must start the provider flow"


async def test_existing_email_with_correct_password_reaches_home(
    login_page: LoginPage, login_account: TestAccount
) -> None:
    """2 - Existing email with correct password reaches Home"""
    home = await login_page.login(login_account.email, login_account.password)
    assert await home.is_welcome_message_visible()


async def test_invalid_email_password_login_attempts_are_rejected(
    login_page: LoginPage, login_account: TestAccount, accounts: TestAccounts
) -> None:
    """3 - Invalid email/password login attempts are rejected"""
    unknown = accounts.unknown_account()

    # Existing email with empty password
    await assert_login_rejected(login_page, login_account.email, "", BAD_CREDENTIALS_MESSAGE)
    # Unknown email
    await assert_login_rejected(login_page, unknown.email, unknown.password, BAD_CREDENTIALS_MESSAGE)
    # Empty credentials
    await assert_login_rejected(login_page, "", "", INVALID_EMAIL_MESSAGE)
    # Existing email with incorrect password
    await assert_login_rejected(login_page, login_account.email, unknown.password, BAD_CREDENTIALS_MESSAGE)
