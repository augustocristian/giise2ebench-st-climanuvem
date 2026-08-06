# -*- coding: utf-8 -*-
"""Page Object for the Register form. Constructing this object waits until
the username input is visible. Mirrors selenium-java's ``RegisterPage``.
"""
from climanuvem.pages.base_page import BasePage

REGISTER_FEEDBACK_KEYWORDS = (
    "error",
    "inválid",
    "invalid",
    "contraseña",
    "correo",
    "usuario",
    "coincid",
    "uso",
    "obligatorio",
    "requerid",
)
VERIFY_DIALOG_KEYWORDS = ("verific", "correo")


class RegisterPage(BasePage):
    USERNAME_INPUT = BasePage.input_by_placeholder("Nombre de usuario")
    EMAIL_INPUT = BasePage.input_by_placeholder("Correo electrónico")
    PASSWORD_INPUT = BasePage.input_by_placeholder("Contraseña")
    CONFIRM_PASSWORD_INPUT = BasePage.input_by_placeholder("Confirmar contraseña")
    LOGIN_LINK = BasePage.by_partial_text("Inicia sesión")
    SUBMIT_BUTTON = BasePage.by_xpath(
        "//*[@role='button' or self::button or @tabindex]"
        "[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ','abcdefghijklmnopqrstuvwxyzáéíóúüñ'),'registr')"
        " or contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ','abcdefghijklmnopqrstuvwxyzáéíóúüñ'),'crear')]"
    )
    HOME_MARKER = BasePage.by_partial_text("Bienvenido")

    def __init__(self, session):
        super().__init__(session)
        self.wait_for(self.USERNAME_INPUT)

    # ── Queries ──────────────────────────────────────────────────────────

    def is_username_input_present(self) -> bool:
        return self.is_present(self.USERNAME_INPUT)

    def is_email_input_present(self) -> bool:
        return self.is_present(self.EMAIL_INPUT)

    def is_password_input_present(self) -> bool:
        return self.is_present(self.PASSWORD_INPUT)

    def is_confirm_password_input_present(self) -> bool:
        return self.is_present(self.CONFIRM_PASSWORD_INPUT)

    def is_login_link_present(self) -> bool:
        return self.is_present(self.LOGIN_LINK)

    def is_home_visible(self) -> bool:
        return self.is_present(self.HOME_MARKER)

    def is_verification_dialog_visible(self) -> bool:
        return self.body_text_contains_any(VERIFY_DIALOG_KEYWORDS[:1]) and self.body_text_contains_any(
            VERIFY_DIALOG_KEYWORDS[1:]
        )

    def has_register_error_or_validation(self) -> bool:
        return self.body_text_contains_any(REGISTER_FEEDBACK_KEYWORDS) or self.has_invalid_required_input()

    # ── Actions ──────────────────────────────────────────────────────────

    def enter_username(self, username: str) -> "RegisterPage":
        self.fill(self.USERNAME_INPUT, username)
        return self

    def enter_email(self, email: str) -> "RegisterPage":
        self.fill(self.EMAIL_INPUT, email)
        return self

    def enter_password(self, password: str) -> "RegisterPage":
        self.fill(self.PASSWORD_INPUT, password)
        return self

    def enter_confirm_password(self, password: str) -> "RegisterPage":
        self.fill(self.CONFIRM_PASSWORD_INPUT, password)
        return self

    def submit_register(self) -> "RegisterPage":
        self.click_last_visible(self.SUBMIT_BUTTON)
        return self

    def register(self, username: str, email: str, password: str, confirm_password: str) -> "RegisterPage":
        self.enter_username(username)
        self.enter_email(email)
        self.enter_password(password)
        self.enter_confirm_password(confirm_password)
        return self.submit_register()

    def wait_for_home(self):
        from climanuvem.pages.home_page import HomePage

        self.wait_for(self.HOME_MARKER)
        return HomePage(self._session)

    def wait_for_verification_dialog(self) -> "RegisterPage":
        predicate = (
            "() => {"
            "const lower = document.body.innerText.toLowerCase();"
            "return lower.includes('verific') && lower.includes('correo');"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))
        return self

    def wait_for_register_failure(self) -> "RegisterPage":
        keywords_js = "[" + ",".join(f"'{keyword}'" for keyword in REGISTER_FEEDBACK_KEYWORDS) + "]"
        predicate = (
            "() => {"
            "const lower = document.body.innerText.toLowerCase();"
            f"const feedback = {keywords_js}.some(k => lower.includes(k));"
            "const invalid = Array.from(document.querySelectorAll('input'))"
            ".some(el => el.required && !el.checkValidity());"
            f"const usernamePresent = !!document.querySelector('{self.USERNAME_INPUT.value}');"
            "return (feedback || invalid) && usernamePresent;"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))
        return self

    def click_login_link(self):
        """Navigates back to the Login form."""
        from climanuvem.pages.login_page import LoginPage

        self.click(self.LOGIN_LINK)
        return LoginPage(self._session)
