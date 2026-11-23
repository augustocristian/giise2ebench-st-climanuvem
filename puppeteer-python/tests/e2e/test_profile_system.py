"""Browser system tests for profile configuration.

Mirrors ``ProfileSystemTests`` of playwright-csharp (derived from selenium-java's ``TestProfileSystem``):
every profile account gets its own isolated browser context, so no manual session cleanup is needed.
"""
import pytest
import pytest_asyncio

from climanuvem.common import TestAccount, TestAccounts
from climanuvem.pages import HomePage, LoginPage, ProfilePage
from climanuvem.pages.profile_page import LanguageOption, ThemeOption

USERNAME_0 = ""
USERNAME_2 = "ab"
USERNAME_20_A = "perfilPrueba12345678"
USERNAME_20_B = "perfilPrueba87654321"
USERNAME_21 = "perfilPrueba123456789"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Runs every test that asks for ``profile_account`` once per ``profile_user`` row of the accounts file."""
    if "profile_account" not in metafunc.fixturenames:
        return
    try:
        params = [pytest.param(account, id=account.email) for account in TestAccounts.load().profile_accounts()]
    except (FileNotFoundError, LookupError):  # no accounts configured: fail the tests, not the collection
        params = [pytest.param(None, id="no-profile-accounts")]
    metafunc.parametrize("profile_account", params, indirect=True)


@pytest.fixture
def profile_account(request: pytest.FixtureRequest) -> TestAccount:
    """One verified account for profile tests (parametrized by ``pytest_generate_tests``)."""
    if request.param is None:
        pytest.fail("Configure at least one profile_user in ACCOUNTS_FILE (see tests/resources/accounts.template.csv).")
    return request.param


@pytest_asyncio.fixture(loop_scope="session")
async def guest_profile(home_page: HomePage) -> ProfilePage:
    """Profile screen of a guest session."""
    profile = await home_page.open_profile()
    await profile.expect_guest_view()
    return profile


@pytest_asyncio.fixture(loop_scope="session")
async def authenticated_profile(login_page: LoginPage, profile_account: TestAccount) -> ProfilePage:
    """Profile screen of a logged-in profile account."""
    home = await login_page.login(profile_account.email, profile_account.password)
    profile = await home.open_profile()
    await profile.expect_authenticated_view()
    return profile


async def assert_theme_and_language_preferences_selectable(profile: ProfilePage) -> None:
    """Every theme and language option can be chosen and is persisted."""
    for theme in ThemeOption:
        await profile.choose_theme(theme)
        await profile.expect_stored_theme(theme)
    for language in LanguageOption:
        await profile.choose_language(language)
        await profile.expect_stored_language(language)


async def test_guest_session_theme_and_language_preferences_can_be_selected(guest_profile: ProfilePage) -> None:
    """Guest session - theme and language preferences can be selected"""
    await assert_theme_and_language_preferences_selectable(guest_profile)


async def test_guest_session_shows_guest_label_instead_of_email(guest_profile: ProfilePage) -> None:
    """Guest session - the profile shows no account email"""
    assert "@" not in await guest_profile.displayed_email()


async def test_authenticated_session_shows_the_account_email(
    authenticated_profile: ProfilePage, profile_account: TestAccount,
) -> None:
    """Authenticated session - the profile shows the email of the logged-in account"""
    assert await authenticated_profile.displayed_email() == profile_account.email


async def test_authenticated_delete_account_shows_confirmation_and_can_be_cancelled(
    authenticated_profile: ProfilePage,
) -> None:
    """Authenticated session - delete account opens confirmation and can be cancelled"""
    await authenticated_profile.open_delete_account_dialog()
    await authenticated_profile.expect_feedback("Delete Account?", "permanent")

    await authenticated_profile.cancel_delete_account()


async def test_authenticated_username_length_rules_are_enforced(authenticated_profile: ProfilePage) -> None:
    """Authenticated session - username length rules are enforced"""
    current_username = await authenticated_profile.current_username()
    await authenticated_profile.save_username(USERNAME_20_B if current_username == USERNAME_20_A else USERNAME_20_A)
    await authenticated_profile.expect_feedback("Profile updated", "updated successfully")
    await authenticated_profile.dismiss_feedback()
    await authenticated_profile.expect_username_section_visible()

    # Zero, two and twenty-one characters keep the save action disabled.
    for invalid_username in (USERNAME_0, USERNAME_2, USERNAME_21):
        await authenticated_profile.set_username(invalid_username)
        await authenticated_profile.expect_save_disabled()


async def test_authenticated_theme_and_language_preferences_can_be_selected(
    authenticated_profile: ProfilePage,
) -> None:
    """Authenticated session - theme and language preferences can be selected"""
    await assert_theme_and_language_preferences_selectable(authenticated_profile)
