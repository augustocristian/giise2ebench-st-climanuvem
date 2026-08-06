# -*- coding: utf-8 -*-
"""Page Object for the Capture (image-upload) screen. Constructing this
object waits until the "Tomar Foto" card is visible. Mirrors
selenium-java's ``CapturePage``.
"""
from climanuvem.pages.base_page import BasePage


class CapturePage(BasePage):
    CAMERA_CARD = BasePage.by_partial_text("Tomar Foto")
    GALLERY_CARD = BasePage.by_partial_text("Galería")
    EXPLAINABILITY = BasePage.by_partial_text("Explicabilidad")
    FORMATS_INFO = BasePage.by_partial_text("Formatos soportados")
    PAGE_HEADER = BasePage.by_partial_text("Analizar Imagen")

    def __init__(self, session):
        super().__init__(session)
        self.wait_for(self.CAMERA_CARD)

    # ── Queries ──────────────────────────────────────────────────────────

    def is_camera_option_visible(self) -> bool:
        return self.is_present(self.CAMERA_CARD)

    def is_gallery_option_visible(self) -> bool:
        return self.is_present(self.GALLERY_CARD)

    def is_explainability_visible(self) -> bool:
        return self.is_present(self.EXPLAINABILITY)

    def is_formats_info_visible(self) -> bool:
        return self.is_present(self.FORMATS_INFO)

    def is_page_header_visible(self) -> bool:
        return self.is_present(self.PAGE_HEADER)
