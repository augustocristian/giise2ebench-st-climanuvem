# -*- coding: utf-8 -*-
"""API tests for the image-upload endpoint, mirroring selenium-java's
``TestApiAnalysis``:
  - POST /analysis/upload — creates an analysis record and returns its ID
Runs with DISABLE_WORKER=true, so uploaded analyses remain in 'analyzing'
status — no Ollama connection is required.
"""
import logging
import unittest

from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)


class TestApiAnalysis(ApiTestCase):

    def test_upload_image_returns_analyzing_status(self):
        logger.debug("Starting the test: " + self._testMethodName)
        image = self.create_test_image()
        response = self.upload_image(self.analysis_url("/upload"), image, "Test Location")
        body = response.json()

        assert "analysis_id" in body
        assert body.get("status") == "analyzing"
        assert body.get("analysis_id") > 0
        logger.debug("Ending the test: " + self._testMethodName)

    def test_upload_image_http_status(self):
        logger.debug("Starting the test: " + self._testMethodName)
        image = self.create_test_image()
        status = self.upload_image_status(self.analysis_url("/upload"), image, "Another Location")
        assert status == 200
        logger.debug("Ending the test: " + self._testMethodName)

    def test_upload_with_custom_location(self):
        logger.debug("Starting the test: " + self._testMethodName)
        location = f"Madrid, Spain {self.unique()}"
        image = self.create_test_image()
        response = self.upload_image(self.analysis_url("/upload"), image, location)
        body = response.json()

        assert "analysis_id" in body
        assert body.get("analysis_id") > 0
        logger.debug("Ending the test: " + self._testMethodName)

    def test_consecutive_uploads_have_distinct_ids(self):
        logger.debug("Starting the test: " + self._testMethodName)
        id_one = self.create_analysis("Location A")
        id_two = self.create_analysis("Location B")
        assert id_one != id_two
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
