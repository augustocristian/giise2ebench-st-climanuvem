# -*- coding: utf-8 -*-
"""Browser system tests for profile configuration, derived from the same
hierarchical test design as selenium-java's ``TestProfileSystem``.

The parameterized authenticated scenarios open a *dedicated* incognito
BrowserSession per account (see ``_authenticated_profile``) instead of
reusing the class-level ``self.session`` the guest scenario relies on —
each account must start from a logged-out Welcome screen, and Firebase's
persisted session would otherwise carry over between accounts within the
same test method (selenium-java sidesteps this entirely because JUnit's
``@ParameterizedTest`` re-runs ``@BeforeEach`` — a fresh ChromeDriver — for
every row).
"""
import logging
import unittest
from contextlib import contextmanager

from climanuvem.common.browser_session import BrowserSession, BrowserTestCase
from climanuvem.pages import WelcomePage

logger = logging.getLogger(__name__)

USERNAME_0 = ""
USERNAME_2 = "ab"
USERNAME_20_A = "perfilPrueba12345678"
USERNAME_20_B = "perfilPrueba87654321"
USERNAME_21 = "perfilPrueba123456789"


def _username_20_different_from(current_username: str) -> str:
    return USERNAME_20_B if current_username == USERNAME_20_A else USERNAME_20_A


class TestProfileSystem(BrowserTestCase):

    def test_guest_session_theme_and_language_preferences_can_be_selected(self):
        """Guest session - theme and language preferences can be selected"""
        logger.debug("Starting the test: " + self._testMethodName)
        profile_page = self._open_guest_profile()
        self._assert_theme_and_language_preferences_selectable(profile_page)
        logger.debug("Ending the test: " + self._testMethodName)

    def test_authenticated_delete_account_shows_confirmation_and_can_be_cancelled(self):
        """Authenticated session - delete account opens confirmation and can be cancelled"""
        logger.debug("Starting the test: " + self._testMethodName)
        for account in self.test_accounts.profile_accounts():
            with self.subTest(account=str(account)):
                with self._authenticated_profile(account) as profile_page:
                    profile_page.open_delete_account_dialog()
                    assert profile_page.is_delete_confirm_visible(), (
                        "Delete account must open a confirmation dialog"
                    )

                    profile_page.cancel_delete_account()
                    assert not profile_page.is_delete_confirm_visible(), (
                        "Delete confirmation must close after cancelling"
                    )
        logger.debug("Ending the test: " + self._testMethodName)

    def test_authenticated_username_length_rules_are_enforced(self):
        """Authenticated session - username length rules are enforced"""
        logger.debug("Starting the test: " + self._testMethodName)
        for account in self.test_accounts.profile_accounts():
            with self.subTest(account=str(account)):
                with self._authenticated_profile(account) as profile_page:
                    valid_username_20 = _username_20_different_from(profile_page.current_username())

                    profile_page.update_username(valid_username_20).wait_for_profile_feedback().close_profile_feedback()
                    assert profile_page.is_username_section_visible(), (
                        "Twenty-character username must be accepted and keep the user on Profile"
                    )

                    profile_page.set_username(USERNAME_0)
                    assert not profile_page.is_save_button_enabled(), (
                        "Zero-character username must keep the save action disabled"
                    )

                    profile_page.set_username(USERNAME_2)
                    assert not profile_page.is_save_button_enabled(), (
                        "Two-character username must keep the save action disabled"
                    )

                    profile_page.set_username(USERNAME_21)
                    assert not profile_page.is_save_button_enabled(), (
                        "Twenty-one-character username must keep the save action disabled"
                    )
        logger.debug("Ending the test: " + self._testMethodName)

    def test_authenticated_theme_and_language_preferences_can_be_selected(self):
        """Authenticated session - theme and language preferences can be selected"""
        logger.debug("Starting the test: " + self._testMethodName)
        for account in self.test_accounts.profile_accounts():
            with self.subTest(account=str(account)):
                with self._authenticated_profile(account) as profile_page:
                    self._assert_theme_and_language_preferences_selectable(profile_page)
        logger.debug("Ending the test: " + self._testMethodName)

    # ── Internals ────────────────────────────────────────────────────────

    def _open_guest_profile(self):
        profile_page = self.login_as_guest().click_profile().wait_for_guest_profile()
        assert profile_page.is_guest_preferences_visible(), "Guest profile must show guest preferences"
        return profile_page

    @contextmanager
    def _authenticated_profile(self, account):
        session = BrowserSession()
        try:
            session.run(session.page.goto(self.frontend_url))
            profile_page = (
                WelcomePage(session)
                .click_login_button()
                .login(account.email, account.password)
                .wait_for_home()
                .click_profile()
                .wait_for_authenticated_profile()
            )
            assert profile_page.is_username_section_visible(), (
                "Authenticated profile must show username configuration"
            )
            assert profile_page.is_delete_account_visible(), "Authenticated profile must show delete-account action"
            yield profile_page
        finally:
            session.close()

    @staticmethod
    def _assert_theme_and_language_preferences_selectable(profile_page):
        profile_page.choose_light_theme()
        assert profile_page.has_stored_theme("light"), "Profile must store the light theme preference"

        profile_page.choose_dark_theme()
        assert profile_page.has_stored_theme("dark"), "Profile must store the dark theme preference"

        profile_page.choose_system_theme()
        assert profile_page.has_stored_theme("system"), "Profile must store the system theme preference"

        profile_page.choose_english_language()
        assert profile_page.has_stored_language("en"), "Profile must store the English language preference"

        profile_page.choose_spanish_language()
        assert profile_page.has_stored_language("es"), "Profile must store the Spanish language preference"

        profile_page.choose_system_language()
        assert profile_page.has_stored_language("system"), "Profile must store the system language preference"


if __name__ == '__main__':
    unittest.main()
