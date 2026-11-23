"""Register form."""
from climanuvem.browser import TestId
from climanuvem.common.test_ids import Register
from climanuvem.pages.base_page import BasePage


class RegisterPage(BasePage):
    FEEDBACK_ID = Register.FEEDBACK
    USERNAME_INPUT = TestId.of(Register.USERNAME_INPUT)
    EMAIL_INPUT = TestId.of(Register.EMAIL_INPUT)
    PASSWORD_INPUT = TestId.of(Register.PASSWORD_INPUT)
    CONFIRM_PASSWORD_INPUT = TestId.of(Register.CONFIRM_PASSWORD_INPUT)
    SUBMIT_BUTTON = TestId.of(Register.SUBMIT_BUTTON)

    async def _wait_ready(self) -> None:
        await self.locator(self.USERNAME_INPUT).wait_for("visible")

    async def type_username(self, username: str) -> str:
        """Types into the username field and returns the stored value, which the input caps at its max length."""
        await self.fill(self.USERNAME_INPUT, username)
        return await self.locator(self.USERNAME_INPUT).input_value()

    async def register(self, username: str, email: str, password: str, confirm_password: str) -> None:
        """Fills the whole form and submits it without waiting for a result."""
        await self.fill(self.USERNAME_INPUT, username)
        await self.fill(self.EMAIL_INPUT, email)
        await self.fill(self.PASSWORD_INPUT, password)
        await self.fill(self.CONFIRM_PASSWORD_INPUT, confirm_password)
        await self.click(self.SUBMIT_BUTTON)
