# -*- coding: utf-8 -*-
"""Page Object for the Login form. Constructing this object waits until
the email input is visible. Mirrors selenium-java's ``LoginPage``.
"""
import asyncio
import time

from climanuvem.pages.base_page import BasePage

FEEDBACK_KEYWORDS = ("error", "incorrect", "credencial", "obligatorio", "requerid")


class LoginPage(BasePage):
    EMAIL_INPUT = BasePage.input_by_placeholder("Correo electrónico")
    PASSWORD_INPUT = BasePage.input_by_placeholder("Contraseña")
    FORGOT_PASSWORD = BasePage.by_partial_text("Olvidaste tu contraseña")
    REGISTER_LINK = BasePage.by_partial_text("Regístrate")
    SUBMIT_BUTTON = BasePage.by_xpath(
        "//*[@role='button' or self::button or @tabindex][contains(normalize-space(.),'Iniciar Sesión')]"
    )
    GOOGLE_BUTTON = BasePage.by_partial_text("Google")
    HOME_MARKER = BasePage.by_partial_text("Bienvenido")
    ACCEPT_BUTTON = BasePage.by_xpath(
        "//*[@role='button' or self::button or @tabindex]"
        "[contains(normalize-space(.),'Aceptar') or contains(normalize-space(.),'Accept') "
        "or contains(normalize-space(.),'OK')]"
    )

    def __init__(self, session):
        super().__init__(session)
        self.wait_for(self.EMAIL_INPUT)

    # ── Queries ──────────────────────────────────────────────────────────

    def is_email_input_present(self) -> bool:
        return self.is_present(self.EMAIL_INPUT)

    def is_password_input_present(self) -> bool:
        return self.is_present(self.PASSWORD_INPUT)

    def is_forgot_password_present(self) -> bool:
        return self.is_present(self.FORGOT_PASSWORD)

    def is_register_link_present(self) -> bool:
        return self.is_present(self.REGISTER_LINK)

    def is_google_login_present(self) -> bool:
        return self.is_present(self.GOOGLE_BUTTON)

    def is_home_visible(self) -> bool:
        return self.is_present(self.HOME_MARKER)

    def get_email_value(self) -> str:
        return self.input_value(self.EMAIL_INPUT)

    def has_login_error_or_validation(self) -> bool:
        return self.body_text_contains_any(FEEDBACK_KEYWORDS) or self.has_invalid_required_input()

    # ── Actions ──────────────────────────────────────────────────────────

    def enter_email(self, email: str) -> "LoginPage":
        self.fill(self.EMAIL_INPUT, email)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.fill(self.PASSWORD_INPUT, password)
        return self

    def submit_login(self) -> "LoginPage":
        """Submits the email/password login form and stays on this page object."""
        self.click_last_visible(self.SUBMIT_BUTTON)
        return self

    def login(self, email: str, password: str) -> "LoginPage":
        """Fills both fields and submits the email/password login form."""
        self.enter_email(email)
        self.enter_password(password)
        return self.submit_login()

    def wait_for_home(self):
        """Waits until the authenticated Home screen is visible and returns its page object."""
        from climanuvem.pages.home_page import HomePage

        try:
            self.wait_for_login_settled()
        except Exception as exc:  # pyppeteer.errors.TimeoutError
            raise AssertionError(
                "Login did not reach Home before timeout. Check account credentials in ACCOUNTS_FILE."
            ) from exc

        if self.has_login_error_or_validation() and not self.is_present(self.HOME_MARKER):
            raise AssertionError("Login failed before reaching Home. Check account credentials in ACCOUNTS_FILE.")
        return HomePage(self._session)

    def wait_for_login_settled(self, timeout: int = 30_000) -> None:
        """Polls until either the Home screen or a login error/validation appears."""
        keywords_js = "[" + ",".join(f"'{keyword}'" for keyword in FEEDBACK_KEYWORDS) + "]"
        predicate = (
            "() => {"
            "const text = document.body.innerText;"
            "const home = text.includes('Bienvenido');"
            f"const lower = text.toLowerCase();"
            f"const feedback = {keywords_js}.some(k => lower.includes(k));"
            "const invalid = Array.from(document.querySelectorAll('input'))"
            ".some(el => el.required && !el.checkValidity());"
            "return home || feedback || invalid;"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": timeout}))

    def wait_for_login_failure(self) -> "LoginPage":
        """Waits until the login attempt is rejected by UI validation or an error message."""
        keywords_js = "[" + ",".join(f"'{keyword}'" for keyword in FEEDBACK_KEYWORDS) + "]"
        predicate = (
            "() => {"
            "const lower = document.body.innerText.toLowerCase();"
            f"const feedback = {keywords_js}.some(k => lower.includes(k));"
            "const invalid = Array.from(document.querySelectorAll('input'))"
            ".some(el => el.required && !el.checkValidity());"
            f"const emailPresent = !!document.querySelector('{self.EMAIL_INPUT.value}');"
            "return (feedback || invalid) && emailPresent;"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))
        return self

    def close_login_feedback_if_present(self) -> "LoginPage":
        button = self._last_visible(self._find_all(self.ACCEPT_BUTTON), required=False)
        if button is not None:
            self._run(button.click())
        return self

    def click_google_login_starts_provider(self) -> bool:
        """Starts the Google provider flow without requiring credentials. The flow is
        considered started when a provider window/tab opens or the current page URL
        or body contains a Google/Firebase identity marker."""
        pages_before = len(self._run(self._session.context.pages()))
        self.click(self.GOOGLE_BUTTON)

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            pages_now = len(self._run(self._session.context.pages()))
            if pages_now > pages_before or self._contains_identity_provider_marker():
                return True
            self._run(asyncio.sleep(0.2))
        return self._contains_identity_provider_marker()

    def _contains_identity_provider_marker(self) -> bool:
        url = self._run(self._page.evaluate("() => window.location.href")).lower()
        body = self._run(self._page.evaluate("() => document.body.innerText")).lower()
        return (
            any(marker in url for marker in ("google", "firebase", "identitytoolkit"))
            or "google" in body
            or "firebase" in body
        )

    def click_register_link(self):
        """Clicks "¿No tienes cuenta? Regístrate" and waits for the Register form."""
        from climanuvem.pages.register_page import RegisterPage

        self.click(self.REGISTER_LINK)
        return RegisterPage(self._session)
