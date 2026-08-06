# -*- coding: utf-8 -*-
"""Page Object for profile configuration — mirrors both guest and
authenticated states, and both Spanish/English labels (the language
switcher changes the UI mid-test). Mirrors selenium-java's ``ProfilePage``.
"""
from climanuvem.pages.base_page import BasePage, Locator

STATUS_FEEDBACK_KEYWORDS = (
    "perfil actualizado",
    "profile updated",
    "fallo de seguridad",
    "security failure",
    "error al eliminar datos",
    "error deleting data",
    "nombre de usuario debe tener",
    "username must be between",
)


def _any_text(es: str, en: str) -> Locator:
    return BasePage.by_xpath(f"//*[contains(normalize-space(.),'{es}') or contains(normalize-space(.),'{en}')]")


def _any_interactive_text(es: str, en: str) -> Locator:
    return BasePage.by_xpath(
        "//*[@role='button' or self::button or @tabindex]"
        f"[contains(normalize-space(.),'{es}') or contains(normalize-space(.),'{en}')]"
    )


def _keywords_js(keywords) -> str:
    return "[" + ",".join(f"'{keyword}'" for keyword in keywords) + "]"


class ProfilePage(BasePage):
    PROFILE_TITLE = _any_text("Mi Perfil", "My Profile")
    GUEST_PREFS = _any_text("Preferencias de invitado", "Guest preferences")
    USERNAME_SECTION = _any_text("Nombre de usuario", "Username")
    DELETE_ACCOUNT = _any_interactive_text("Eliminar Cuenta", "Delete Account")
    CONFIRM_DELETE = _any_interactive_text("Sí, eliminar", "Yes, delete")
    CANCEL = _any_interactive_text("Cancelar", "Cancel")
    ACCEPT = BasePage.by_xpath(
        "//*[@role='button' or self::button or @tabindex]"
        "[contains(normalize-space(.),'Aceptar') or contains(normalize-space(.),'Accept') "
        "or contains(normalize-space(.),'OK')]"
    )
    USERNAME_INPUT = Locator("css", 'input[placeholder="Escribe tu nombre"],input[placeholder="Enter your name"]')
    SAVE_BUTTON = _any_interactive_text("Guardar Cambios", "Save Changes")

    def __init__(self, session):
        super().__init__(session)
        self.wait_for(self.PROFILE_TITLE)

    # ── Queries ──────────────────────────────────────────────────────────

    def is_guest_preferences_visible(self) -> bool:
        return self.is_visible(self.GUEST_PREFS)

    def is_username_section_visible(self) -> bool:
        return self.is_visible(self.USERNAME_SECTION)

    def is_delete_account_visible(self) -> bool:
        return self.is_visible(self.DELETE_ACCOUNT)

    def is_delete_confirm_visible(self) -> bool:
        return self.is_visible(self.CONFIRM_DELETE)

    def current_username(self) -> str:
        return self.input_value(self.USERNAME_INPUT)

    def is_save_button_enabled(self) -> bool:
        element = self.wait_for(self.SAVE_BUTTON)
        script = (
            "(el) => {"
            "const target = el.closest(`[role='button'],button,[tabindex]`) || el;"
            "return target.getAttribute('aria-disabled') === 'true'"
            " || target.disabled === true"
            " || window.getComputedStyle(target).pointerEvents === 'none';"
            "}"
        )
        disabled = self._run(self._page.evaluate(script, element))
        return not disabled

    def has_stored_theme(self, value: str) -> bool:
        return self._stored_value("appTheme") == value

    def has_stored_language(self, value: str) -> bool:
        return self._stored_value("appLanguage") == value

    # ── Actions ──────────────────────────────────────────────────────────

    def wait_for_guest_profile(self) -> "ProfilePage":
        self.wait_for(self.GUEST_PREFS)
        return self

    def wait_for_authenticated_profile(self) -> "ProfilePage":
        self.wait_for(self.USERNAME_SECTION)
        self.wait_for(self.DELETE_ACCOUNT)
        return self

    def choose_light_theme(self) -> "ProfilePage":
        return self._choose_theme("Claro", "Light", "light")

    def choose_dark_theme(self) -> "ProfilePage":
        return self._choose_theme("Oscuro", "Dark", "dark")

    def choose_system_theme(self) -> "ProfilePage":
        self._select_option("Sistema", "System", last=False)
        self._wait_for_stored_value("appTheme", "system")
        return self

    def choose_english_language(self) -> "ProfilePage":
        self._select_option("Inglés", "English", last=False)
        self._wait_for_stored_value("appLanguage", "en")
        return self

    def choose_spanish_language(self) -> "ProfilePage":
        self._select_option("Español", "Spanish", last=False)
        self._wait_for_stored_value("appLanguage", "es")
        return self

    def choose_system_language(self) -> "ProfilePage":
        # "Sistema"/"System" appears once under theme options and once under language
        # options — `last=True` picks the language one, mirroring the Java page
        # object's `lastMatch` flag on ProfilePage#clickOption.
        self._select_option("Sistema", "System", last=True)
        self._wait_for_stored_value("appLanguage", "system")
        return self

    def set_username(self, username: str) -> "ProfilePage":
        self.fill(self.USERNAME_INPUT, username)
        return self

    def update_username(self, username: str) -> "ProfilePage":
        self.set_username(username)
        self.click(self.SAVE_BUTTON)
        return self

    def wait_for_profile_feedback(self) -> "ProfilePage":
        predicate = (
            "() => {"
            "const lower = document.body.innerText.toLowerCase();"
            f"return {_keywords_js(STATUS_FEEDBACK_KEYWORDS)}.some(k => lower.includes(k));"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))
        return self

    def close_profile_feedback(self) -> "ProfilePage":
        self.click(self.ACCEPT)
        predicate = (
            "() => {"
            "const lower = document.body.innerText.toLowerCase();"
            f"return !{_keywords_js(STATUS_FEEDBACK_KEYWORDS)}.some(k => lower.includes(k));"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))
        return self

    def open_delete_account_dialog(self) -> "ProfilePage":
        self.click_last_visible(self.DELETE_ACCOUNT)
        self.wait_for(self.CONFIRM_DELETE)
        return self

    def cancel_delete_account(self) -> "ProfilePage":
        self.click(self.CANCEL)
        predicate = (
            "() => {"
            "const text = document.body.innerText;"
            "return !text.includes('Sí, eliminar') && !text.includes('Yes, delete');"
            "}"
        )
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))
        return self

    # ── Internals ────────────────────────────────────────────────────────

    def _choose_theme(self, es: str, en: str, stored_value: str) -> "ProfilePage":
        self._select_option(es, en, last=False)
        self._wait_for_stored_value("appTheme", stored_value)
        return self

    def _select_option(self, es: str, en: str, last: bool) -> None:
        locator = _any_interactive_text(es, en)
        elements = self._find_all(locator)
        visible = [element for element in elements if self._run(element.boundingBox()) is not None]
        if not visible:
            raise AssertionError(f"No visible option matching '{es}'/'{en}'")
        target = visible[-1] if last else visible[0]
        self._run(target.click())

    def _wait_for_stored_value(self, key: str, expected: str) -> None:
        predicate = f"() => window.localStorage.getItem('{key}') === '{expected}'"
        self._run(self._page.waitForFunction(predicate, {"timeout": 30_000}))

    def _stored_value(self, key: str):
        return self._run(self._page.evaluate("(k) => window.localStorage.getItem(k)", key))
