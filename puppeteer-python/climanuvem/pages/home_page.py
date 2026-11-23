"""Home screen, shown after a successful login."""
from typing import TYPE_CHECKING

from climanuvem.browser import TestId
from climanuvem.common.test_ids import Home
from climanuvem.pages.base_page import BasePage

if TYPE_CHECKING:  # the screens link to each other, so they are imported lazily at runtime
    from climanuvem.pages.capture_page import CapturePage
    from climanuvem.pages.profile_page import ProfilePage
    from climanuvem.pages.welcome_page import WelcomePage


class HomePage(BasePage):
    WELCOME = TestId.of(Home.WELCOME)
    ANALYZE_CARD = TestId.of(Home.ANALYZE_CARD)
    LOGOUT_CARD = TestId.of(Home.LOGOUT_CARD)

    async def _wait_ready(self) -> None:
        await self.locator(self.WELCOME).wait_for("visible")
        await self.locator(self.ANALYZE_CARD).wait_for("visible")

    async def is_welcome_message_visible(self) -> bool:
        return await self.is_visible(self.WELCOME)

    async def open_profile(self) -> "ProfilePage":
        """Opens Profile through the welcome banner, which navigates there."""
        from climanuvem.pages.profile_page import ProfilePage

        await self.click(self.WELCOME)
        return await ProfilePage.create(self.page)

    async def open_capture(self) -> "CapturePage":
        """Opens the image capture screen through the analyze card."""
        from climanuvem.pages.capture_page import CapturePage

        await self.click(self.ANALYZE_CARD)
        return await CapturePage.create(self.page)

    async def logout(self) -> "WelcomePage":
        """Logs out and waits for the Welcome screen."""
        from climanuvem.pages.welcome_page import WelcomePage

        await self.click(self.LOGOUT_CARD)
        return await WelcomePage.create(self.page)
