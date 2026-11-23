"""Page object of the Capture screen, where an analysis starts (camera, gallery, explainability)."""
from climanuvem.browser import TestId
from climanuvem.common.test_ids import Capture
from climanuvem.pages.base_page import BasePage


class CapturePage(BasePage):
    FEEDBACK_ID = Capture.FEEDBACK

    async def _wait_ready(self) -> None:
        await self.locator(TestId.of(Capture.HEADER)).wait_for("visible")

    async def is_camera_option_visible(self) -> bool:
        return await self.is_visible(TestId.of(Capture.CAMERA_CARD))

    async def is_gallery_option_visible(self) -> bool:
        return await self.is_visible(TestId.of(Capture.GALLERY_CARD))

    async def is_explainability_visible(self) -> bool:
        return await self.is_visible(TestId.of(Capture.EXPLAINABILITY))

    async def is_formats_info_visible(self) -> bool:
        return await self.is_visible(TestId.of(Capture.FORMATS_INFO))

    async def is_explainability_warning_visible(self) -> bool:
        return await self.is_visible(TestId.of(Capture.EXPLAINABILITY_WARNING))

    async def toggle_explainability(self) -> None:
        await self.click(TestId.of(Capture.EXPLAINABILITY_SWITCH))
