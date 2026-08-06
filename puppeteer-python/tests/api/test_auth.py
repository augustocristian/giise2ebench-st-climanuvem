# -*- coding: utf-8 -*-
"""API tests for authentication enforcement across the API, mirroring
selenium-java's ``TestApiAuth``:
  - GET  /test                 — requires a valid Bearer token
  - GET  /analysis/history     — requires a valid Bearer token
  - POST /analysis/upload      — requires a valid Bearer token
Missing Authorization header -> HTTP 403 (FastAPI HTTPBearer default).
"""
import logging
import unittest

from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)


class TestApiAuth(ApiTestCase):

    def test_test_endpoint_requires_auth(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status(self.root_url("/test")) == 403
        logger.debug("Ending the test: " + self._testMethodName)

    def test_test_endpoint_with_valid_token(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status_auth(self.root_url("/test")) == 200

        body = self.get_json_auth(self.root_url("/test"))
        assert body.get("message") == "Test successful"
        assert "user" in body
        logger.debug("Ending the test: " + self._testMethodName)

    def test_history_requires_auth(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status(self.analysis_url("/history")) == 403
        logger.debug("Ending the test: " + self._testMethodName)

    def test_upload_requires_auth(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status(self.analysis_url("/upload")) == 403
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
