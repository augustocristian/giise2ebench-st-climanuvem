"""HTTP client for the ClimaNuvem REST API (``/api/v1``).

The SUT runs with ``TEST_MODE=true``: any Bearer token is accepted, so the configured test token authenticates
the test user and a missing ``Authorization`` header is the only unauthenticated case.
"""
import time
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

import requests

from climanuvem.common import config, test_images

API_PREFIX = "/api/v1"
NON_EXISTENT_ID = 2**31 - 1
TERMINAL_STATUSES = ("completed", "cancelled")

T = TypeVar("T")


def poll_until(probe: Callable[[], T], done: Callable[[T], bool], timeout_s: float, poll_s: float = 2.0) -> T:
    """Calls ``probe`` every ``poll_s`` seconds until ``done`` holds or the timeout elapses; returns the last value."""
    deadline = time.monotonic() + timeout_s
    while True:
        value = probe()
        if done(value) or time.monotonic() >= deadline:
            return value
        time.sleep(poll_s)


class ApiClient:
    """One HTTP session against the SUT: a single request helper, a single multipart upload helper and shortcuts."""

    def __init__(self, base_url: str = config.SUT_URL, token: str = config.TEST_TOKEN,
                 timeout_s: float = config.HTTP_TIMEOUT_S) -> None:
        self.base_url = base_url
        self.token = token
        self.timeout_s = timeout_s
        self._session = requests.Session()

    def close(self) -> None:
        self._session.close()

    # URLs (relative to the SUT base URL)

    @staticmethod
    def api_url(path: str = "") -> str:
        """Path under the versioned API prefix; empty or starting with "/"."""
        return API_PREFIX + path

    @staticmethod
    def analyses_url(suffix: str = "") -> str:
        """The analyses collection; ``suffix`` is empty or a query string such as "?page=1"."""
        return ApiClient.api_url("/analyses") + suffix

    @staticmethod
    def analysis_url(analysis_id: int) -> str:
        return ApiClient.api_url(f"/analyses/{analysis_id}")

    @staticmethod
    def image_url(analysis_id: int) -> str:
        return ApiClient.analysis_url(analysis_id) + "/image"

    # Requests

    def send(self, method: str, url: str, *, auth: bool = True, json: Any = None,
             files: Mapping[str, Any] | None = None) -> requests.Response:
        """The single request helper: every call in the suite goes through here."""
        headers = {"Authorization": f"Bearer {self.token}"} if auth else {}
        return self._session.request(
            method, self.base_url + url, headers=headers, json=json, files=files, timeout=self.timeout_s
        )

    def get(self, url: str, *, auth: bool = True) -> requests.Response:
        return self.send("GET", url, auth=auth)

    def delete(self, url: str, *, auth: bool = True) -> requests.Response:
        return self.send("DELETE", url, auth=auth)

    def patch_status(self, url: str, status: str, *, auth: bool = True) -> requests.Response:
        return self.send("PATCH", url, auth=auth, json={"status": status})

    def upload(self, image: bytes | None, location: str = "Test Location", filename: str = "test.jpg",
               content_type: str = "image/jpeg", include_explainability: bool | None = None,
               extra_fields: Mapping[str, str] | None = None, auth: bool = True) -> requests.Response:
        """Multipart ``POST /api/v1/analyses`` with camelCase fields.

        A ``None`` image omits the file part; a ``None`` ``include_explainability`` omits that field.
        """
        fields = {"location": location, **(extra_fields or {})}
        if include_explainability is not None:
            fields["includeExplainability"] = str(include_explainability).lower()
        parts: dict[str, Any] = {name: (None, value) for name, value in fields.items()}
        if image is not None:
            parts["file"] = (filename, image, content_type)
        return self.send("POST", self.analyses_url(), auth=auth, files=parts)

    # Fixtures and shared flows

    def create_analysis(self, location: str) -> int:
        """Uploads a tiny valid JPEG and returns the new analysis id."""
        response = self.upload(test_images.tiny(), location)
        assert response.status_code == 202, f"Upload failed: {response.text}"
        return response.json()["id"]

    def delete_all_analyses(self) -> None:
        """Clears the test user's data."""
        response = self.delete(self.analyses_url())
        assert response.status_code == 204, f"DELETE /analyses must clear the test user's data: {response.text}"

    def list_analyses(self, query: str = "?size=100") -> list[dict]:
        """Lists the test user's analyses (first page of up to 100)."""
        response = self.get(self.analyses_url(query))
        assert response.status_code == 200, response.text
        return response.json()

    def wait_for_terminal_status(self, analysis_id: int, timeout_s: float = config.ANALYSIS_TIMEOUT_S) -> dict:
        """Polls ``GET /analyses/{id}`` until it is completed or cancelled; returns the last analysis seen."""
        def probe() -> dict:
            response = self.get(self.analysis_url(analysis_id))
            assert response.status_code == 200, response.text
            return response.json()

        return poll_until(probe, lambda analysis: analysis["status"] in TERMINAL_STATUSES, timeout_s)
