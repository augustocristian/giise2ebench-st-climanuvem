"""Page object of the Profile screen, in its guest and authenticated variants."""
from enum import Enum

from climanuvem.browser import TestId
from climanuvem.common.test_ids import Profile
from climanuvem.pages.base_page import BasePage


class ThemeOption(Enum):
    """Theme choices: the option's test id and the value stored in ``localStorage``."""

    LIGHT = (Profile.THEME_LIGHT, "light")
    DARK = (Profile.THEME_DARK, "dark")
    SYSTEM = (Profile.THEME_SYSTEM, "system")

    def __init__(self, test_id: str, stored_value: str) -> None:
        self.test_id = test_id
        self.stored_value = stored_value


class LanguageOption(Enum):
    """Language choices: the option's test id and the value stored in ``localStorage``."""

    ENGLISH = (Profile.LANGUAGE_ENGLISH, "en")
    SPANISH = (Profile.LANGUAGE_SPANISH, "es")
    SYSTEM = (Profile.LANGUAGE_SYSTEM, "system")

    def __init__(self, test_id: str, stored_value: str) -> None:
        self.test_id = test_id
        self.stored_value = stored_value


class ProfilePage(BasePage):
    FEEDBACK_ID = Profile.FEEDBACK

    async def _wait_ready(self) -> None:
        await self._wait_visible(Profile.TITLE)

    async def _wait_visible(self, test_id: str) -> None:
        await self.locator(TestId.of(test_id)).wait_for("visible")

    # Views

    async def expect_guest_view(self) -> None:
        """Waits for the guest variant: the guest preferences notice."""
        await self._wait_visible(Profile.GUEST_PREFERENCES)

    async def expect_authenticated_view(self) -> None:
        """Waits for the authenticated variant: username section and delete-account action."""
        await self._wait_visible(Profile.USERNAME_SECTION)
        await self._wait_visible(Profile.DELETE_ACCOUNT_BUTTON)

    async def expect_username_section_visible(self) -> None:
        await self._wait_visible(Profile.USERNAME_SECTION)

    async def displayed_email(self) -> str:
        """Text under the avatar: the account email, or the guest label."""
        return await self.locator(TestId.of(Profile.EMAIL)).text()

    # Username

    async def current_username(self) -> str:
        return await self.locator(TestId.of(Profile.USERNAME_INPUT)).input_value()

    async def set_username(self, username: str) -> None:
        await self.fill(TestId.of(Profile.USERNAME_INPUT), username)

    async def save_username(self, username: str) -> None:
        await self.set_username(username)
        await self.click(TestId.of(Profile.SAVE_BUTTON))

    async def is_save_enabled(self) -> bool:
        """Whether the save button can be pressed (disabled buttons expose ``aria-disabled``)."""
        save_button = self.locator(TestId.of(Profile.SAVE_BUTTON))
        return await save_button.attribute("aria-disabled") != "true"

    async def expect_save_disabled(self) -> None:
        async def disabled() -> bool:
            return not await self.is_save_enabled()

        await self.wait_until(disabled, "the save button to be disabled")

    # Delete account

    async def open_delete_account_dialog(self) -> None:
        await self.click(TestId.of(Profile.DELETE_ACCOUNT_BUTTON))
        await self._wait_visible(Profile.DELETE_CONFIRM_BUTTON)

    async def cancel_delete_account(self) -> None:
        await self.click(TestId.of(Profile.DELETE_CANCEL_BUTTON))
        await self.wait_hidden(self.locator(TestId.of(Profile.DELETE_CONFIRM_BUTTON)))

    # Preferences

    async def choose_theme(self, theme: ThemeOption) -> None:
        await self.click(TestId.of(theme.test_id))

    async def choose_language(self, language: LanguageOption) -> None:
        await self.click(TestId.of(language.test_id))

    async def expect_stored_theme(self, theme: ThemeOption) -> None:
        await self._expect_stored("appTheme", theme.stored_value)

    async def expect_stored_language(self, language: LanguageOption) -> None:
        await self._expect_stored("appLanguage", language.stored_value)

    async def _expect_stored(self, key: str, value: str) -> None:
        async def stored() -> bool:
            return await self.page.evaluate("(k) => window.localStorage.getItem(k)", key) == value

        await self.wait_until(stored, f"localStorage[{key}] to be {value!r}")
