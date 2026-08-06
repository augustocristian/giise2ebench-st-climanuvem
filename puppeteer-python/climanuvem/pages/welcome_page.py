# -*- coding: utf-8 -*-
"""Page Object for the Welcome (root) screen — the first page any visitor
sees. Constructing this object waits until the guest-login button is
visible, guaranteeing the app has fully mounted before any assertion runs.
Mirrors selenium-java's ``WelcomePage``.
"""
from climanuvem.pages.base_page import BasePage


class WelcomePage(BasePage):
    GUEST_BUTTON = BasePage.by_partial_text("Continuar como invitado")
    LOGIN_BUTTON = BasePage.by_partial_text("Iniciar Sesión")
    APP_TITLE = BasePage.by_partial_text("ClimaNuvem")
    TAGLINE = BasePage.by_partial_text("Meteorólogo de bolsillo")
    HOME_MARKER = BasePage.by_partial_text("Bienvenido")

    def __init__(self, session):
        super().__init__(session)
        self.wait_for(self.GUEST_BUTTON)

    # ── Queries ──────────────────────────────────────────────────────────

    def is_app_title_visible(self) -> bool:
        return self.is_present(self.APP_TITLE)

    def is_tagline_visible(self) -> bool:
        return self.is_present(self.TAGLINE)

    def is_login_button_present(self) -> bool:
        return self.is_present(self.LOGIN_BUTTON)

    def is_guest_button_present(self) -> bool:
        return self.is_present(self.GUEST_BUTTON)

    def is_home_visible(self) -> bool:
        return self.is_present(self.HOME_MARKER)

    # ── Actions ──────────────────────────────────────────────────────────

    def click_login_button(self):
        """Clicks "Iniciar Sesión" and waits for the Login form to appear."""
        from climanuvem.pages.login_page import LoginPage

        self.click(self.LOGIN_BUTTON)
        return LoginPage(self._session)

    def click_anonymous_login(self):
        """Clicks "Continuar como invitado", which triggers Firebase anonymous
        auth, and waits for the Home screen to mount."""
        from climanuvem.pages.home_page import HomePage

        self.click(self.GUEST_BUTTON)
        return HomePage(self._session)
