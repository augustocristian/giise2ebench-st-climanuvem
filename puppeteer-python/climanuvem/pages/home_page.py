# -*- coding: utf-8 -*-
"""Page Object for the Home screen — shown after a successful login.
Constructing this object waits until both the welcome message and the
"Analizar Imagen" quick-action card are visible. Mirrors selenium-java's
``HomePage``.
"""
from climanuvem.pages.base_page import BasePage


class HomePage(BasePage):
    WELCOME_MESSAGE = BasePage.by_partial_text("Bienvenido")
    ANALYZE_CARD = BasePage.by_partial_text("Analizar Imagen")
    HISTORY_CARD = BasePage.by_partial_text("Historial")
    LOGOUT_CARD = BasePage.by_partial_text("Cerrar Sesión")

    def __init__(self, session):
        super().__init__(session)
        self.wait_for(self.WELCOME_MESSAGE)
        self.wait_for(self.ANALYZE_CARD)

    # ── Queries ──────────────────────────────────────────────────────────

    def is_welcome_message_visible(self) -> bool:
        return self.is_present(self.WELCOME_MESSAGE)

    def is_analyze_card_visible(self) -> bool:
        return self.is_present(self.ANALYZE_CARD)

    def is_history_card_visible(self) -> bool:
        return self.is_present(self.HISTORY_CARD)

    def is_logout_card_visible(self) -> bool:
        return self.is_present(self.LOGOUT_CARD)

    # ── Actions ──────────────────────────────────────────────────────────

    def click_analyze_image(self):
        """Navigates to the Capture screen."""
        from climanuvem.pages.capture_page import CapturePage

        self.click(self.ANALYZE_CARD)
        return CapturePage(self._session)

    def click_profile(self):
        """Opens Profile through the router URL, avoiding flaky React Native Web card clicks."""
        from climanuvem.pages.profile_page import ProfilePage

        origin = self._run(self._page.evaluate("() => window.location.origin"))
        self._run(self._page.goto(f"{origin}/profile"))
        return ProfilePage(self._session)

    def click_logout(self):
        """Clicks "Cerrar Sesión" and waits for the Welcome screen to re-appear."""
        from climanuvem.pages.welcome_page import WelcomePage

        self.click(self.LOGOUT_CARD)
        return WelcomePage(self._session)
