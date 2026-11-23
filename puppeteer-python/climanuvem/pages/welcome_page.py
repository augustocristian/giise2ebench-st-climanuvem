"""Welcome (root) screen, the first page any visitor sees."""
from climanuvem.browser import TestId
from climanuvem.common.test_ids import Welcome
from climanuvem.pages.base_page import BasePage
from climanuvem.pages.home_page import HomePage
from climanuvem.pages.login_page import LoginPage


class WelcomePage(BasePage):
    LOGIN_BUTTON = TestId.of(Welcome.LOGIN_BUTTON)
    GUEST_BUTTON = TestId.of(Welcome.GUEST_BUTTON)

    async def _wait_ready(self) -> None:
        await self.locator(self.GUEST_BUTTON).wait_for("visible")

    async def click_login_button(self) -> LoginPage:
        await self.click(self.LOGIN_BUTTON)
        return await LoginPage.create(self.page)

    async def click_anonymous_login(self) -> HomePage:
        """Continues as guest (Firebase anonymous auth) and waits for Home."""
        await self.click(self.GUEST_BUTTON)
        return await HomePage.create(self.page)
