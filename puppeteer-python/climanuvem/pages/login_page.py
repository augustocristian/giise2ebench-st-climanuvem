"""Login form."""
from climanuvem.browser import ElementTimeoutError, TestId
from climanuvem.common.test_ids import Login
from climanuvem.pages.base_page import BasePage
from climanuvem.pages.home_page import HomePage
from climanuvem.pages.register_page import RegisterPage

PROVIDER_TIMEOUT_S = 5.0


class LoginPage(BasePage):
    FEEDBACK_ID = Login.FEEDBACK
    EMAIL_INPUT = TestId.of(Login.EMAIL_INPUT)
    PASSWORD_INPUT = TestId.of(Login.PASSWORD_INPUT)
    SUBMIT_BUTTON = TestId.of(Login.SUBMIT_BUTTON)
    GOOGLE_BUTTON = TestId.of(Login.GOOGLE_BUTTON)
    REGISTER_LINK = TestId.of(Login.REGISTER_LINK)

    async def _wait_ready(self) -> None:
        await self.locator(self.EMAIL_INPUT).wait_for("visible")

    async def is_google_login_visible(self) -> bool:
        return await self.is_visible(self.GOOGLE_BUTTON)

    async def submit_credentials(self, email: str, password: str) -> None:
        """Fills both fields and submits the form without waiting for a result."""
        await self.fill(self.EMAIL_INPUT, email)
        await self.fill(self.PASSWORD_INPUT, password)
        await self.click(self.SUBMIT_BUTTON)

    async def login(self, email: str, password: str) -> HomePage:
        """Logs in with valid credentials and waits for Home."""
        await self.submit_credentials(email, password)
        return await HomePage.create(self.page)

    async def open_register(self) -> RegisterPage:
        await self.click(self.REGISTER_LINK)
        return await RegisterPage.create(self.page)

    async def start_google_login(self) -> bool:
        """Clicks "Continue with Google". The provider flow counts as started when the page reports a
        Google-specific dialog or an identity-provider URL (the web build has no provider popup to observe)."""
        await self.click(self.GOOGLE_BUTTON)

        async def provider_flow_started() -> bool:
            url = (await self.page.url()).lower()
            feedback = await self.text_or_empty(self.locator(TestId.of(Login.FEEDBACK)))
            return "google" in url or "firebase" in url or "google" in feedback.lower()

        try:
            await self.wait_until(provider_flow_started, "the Google provider flow to start", PROVIDER_TIMEOUT_S)
        except ElementTimeoutError:
            return False
        return True
