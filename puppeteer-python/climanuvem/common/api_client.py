# -*- coding: utf-8 -*-
"""Base class for the ClimaNuvem API test suite. Handles HTTP plumbing,
Bearer-token auth, multipart image upload, and common fixture creation.
Mirrors selenium-java's ``BaseApiClass``.

The SUT must be started with ``TEST_MODE=true`` so that requests bearing
``test_token`` bypass Firebase verification (see ``sut/docker-compose.test.yml``).
"""
import io
import logging
import time
import unittest
from typing import Optional

import requests
from PIL import Image, ImageDraw

from climanuvem.common import config

logger = logging.getLogger(__name__)

_TOO_LARGE_PAYLOAD_SIZE = 5 * 1024 * 1024 + 1


def _to_jpeg_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


class ApiTestCase(unittest.TestCase):
    """Base class for HTTP-level tests — no browser involved."""

    sut_url = config.SUT_URL
    test_token = config.TEST_TOKEN

    @classmethod
    def setUpClass(cls):
        cls.session = requests.Session()
        logger.info("API base URL: %s", cls.sut_url)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    # ── URL builders ─────────────────────────────────────────────────────

    def analysis_url(self, path: str) -> str:
        return f"{self.sut_url}/analysis{path}"

    def root_url(self, path: str) -> str:
        return f"{self.sut_url}{path}"

    # ── Unauthenticated HTTP ─────────────────────────────────────────────

    def get_status(self, url: str) -> int:
        return self.session.get(url, timeout=config.HTTP_TIMEOUT_S).status_code

    def get_json(self, url: str):
        return self.session.get(url, timeout=config.HTTP_TIMEOUT_S).json()

    # ── Authenticated HTTP ───────────────────────────────────────────────

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.test_token}"}

    def get_status_auth(self, url: str) -> int:
        return self.session.get(url, headers=self._auth_headers(), timeout=config.HTTP_TIMEOUT_S).status_code

    def get_json_auth(self, url: str):
        return self.session.get(url, headers=self._auth_headers(), timeout=config.HTTP_TIMEOUT_S).json()

    def delete_status_auth(self, url: str) -> int:
        return self.session.delete(url, headers=self._auth_headers(), timeout=config.HTTP_TIMEOUT_S).status_code

    def patch_status_auth(self, url: str) -> int:
        return self.session.patch(url, headers=self._auth_headers(), timeout=config.HTTP_TIMEOUT_S).status_code

    # ── Multipart image upload ──────────────────────────────────────────

    def upload_image(
        self,
        url: str,
        image_bytes: bytes,
        location: str,
        filename: str = "test.jpg",
        content_type: str = "image/jpeg",
        include_explainability: Optional[bool] = None,
    ) -> requests.Response:
        data = {"location": location}
        if include_explainability is not None:
            data["include_explainability"] = str(include_explainability)
        files = {"file": (filename, image_bytes, content_type)}
        return self.session.post(
            url, headers=self._auth_headers(), data=data, files=files, timeout=config.HTTP_TIMEOUT_S
        )

    def upload_image_status(self, *args, **kwargs) -> int:
        return self.upload_image(*args, **kwargs).status_code

    def upload_without_file_status(self, url: str, location: str) -> int:
        response = self.session.post(
            url, headers=self._auth_headers(), data={"location": location}, timeout=config.HTTP_TIMEOUT_S
        )
        return response.status_code

    # ── JSON / history helpers ──────────────────────────────────────────

    def find_analysis_in_history(self, analysis_id: int) -> Optional[dict]:
        history = self.get_json_auth(self.analysis_url("/history"))
        for entry in history:
            if entry.get("id") == analysis_id:
                return entry
        return None

    def wait_for_analysis_terminal_status(
        self, analysis_id: int, timeout_ms: Optional[int] = None, poll_ms: int = 5000
    ) -> Optional[dict]:
        timeout_ms = config.ANALYSIS_TIMEOUT_MS if timeout_ms is None else timeout_ms
        deadline = time.monotonic() + timeout_ms / 1000
        last_seen = None

        while time.monotonic() < deadline:
            last_seen = self.find_analysis_in_history(analysis_id)
            if last_seen and last_seen.get("status") in ("completed", "cancelled"):
                return last_seen
            time.sleep(poll_ms / 1000)

        return last_seen

    @staticmethod
    def contains_by_field(items, field: str, expected) -> bool:
        return any(str(item.get(field)) == str(expected) for item in items)

    # ── Test data helpers ────────────────────────────────────────────────

    @staticmethod
    def unique() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def create_test_image() -> bytes:
        """Minimal 10x10 solid JPEG — small and fast, valid enough for the upload endpoint."""
        image = Image.new("RGB", (10, 10), color=(200, 200, 200))
        return _to_jpeg_bytes(image)

    @staticmethod
    def create_cloudy_jpeg() -> bytes:
        image = Image.new("RGB", (640, 360), color=(98, 171, 232))
        draw = ImageDraw.Draw(image)
        draw.ellipse((120, 95, 300, 189), fill=(245, 248, 250))
        draw.ellipse((235, 70, 445, 194), fill=(245, 248, 250))
        draw.ellipse((380, 115, 530, 195), fill=(245, 248, 250))
        draw.rectangle((175, 145, 485, 220), fill=(245, 248, 250))
        draw.ellipse((210, 175, 380, 229), fill=(225, 232, 238))
        return _to_jpeg_bytes(image)

    @staticmethod
    def create_no_cloud_jpeg() -> bytes:
        width, height = 640, 360
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            ratio = y / height
            red = 70 + round(35 * ratio)
            green = 155 + round(45 * ratio)
            blue = 225 + round(25 * ratio)
            draw.line((0, y, width, y), fill=(red, green, blue))
        return _to_jpeg_bytes(image)

    @staticmethod
    def create_empty_image_bytes() -> bytes:
        return b""

    @staticmethod
    def create_too_large_payload() -> bytes:
        """A valid small JPEG followed by junk bytes, padded past the 5 MB upload limit."""
        valid_jpeg = ApiTestCase.create_test_image()
        padding_len = _TOO_LARGE_PAYLOAD_SIZE - len(valid_jpeg)
        pattern = bytes(i % 251 for i in range(251))
        full_cycles, remainder = divmod(padding_len, len(pattern))
        padding = pattern * full_cycles + pattern[:remainder]
        return valid_jpeg + padding

    @staticmethod
    def create_non_jpeg_payload() -> bytes:
        return b"not-a-jpeg-image"

    def create_analysis(self, location: str) -> int:
        """Uploads a test image to POST /analysis/upload and returns the assigned analysis ID."""
        image = self.create_test_image()
        response = self.upload_image(self.analysis_url("/upload"), image, location)
        return response.json()["analysis_id"]

    def delete_all_user_data(self) -> int:
        """Deletes all analysis records for the test user via DELETE /analysis/user-data."""
        status = self.delete_status_auth(self.analysis_url("/user-data"))
        logger.debug("Deleted all user data for test user")
        return status
