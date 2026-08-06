# -*- coding: utf-8 -*-
"""System tests for the real image-analysis flow, mirroring selenium-java's
``TestApiImageAnalysisSystem``.

These tests require the SUT deployed with the analysis worker enabled and
Ollama available (``sut/docker-compose.ollama-test.yml``). Run them
explicitly with:

    REAL_OLLAMA_TESTS=true poetry run pytest tests/api/test_image_analysis_system.py

``unittest.skipUnless`` is the direct equivalent of the Java suite's
``Assumptions.assumeTrue(...)`` opt-in gate: without ``REAL_OLLAMA_TESTS=true``
every test here is reported as skipped, not run.
"""
import logging
import unittest

from climanuvem.common import config
from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)


def _has_normalized_box(cloud_details) -> bool:
    if not cloud_details:
        return False
    for detail in cloud_details:
        box = detail.get("box")
        if not box or len(box) != 4:
            continue
        if all(0.0 <= value <= 1.0 for value in box):
            return True
    return False


def _is_no_cloud_compatible(results) -> bool:
    cloud_types = results.get("cloudTypes") or []
    return not cloud_types or "no_cloud" in cloud_types


_SKIP_REASON = "Real Ollama image-analysis tests are disabled. Set REAL_OLLAMA_TESTS=true to run them."


@unittest.skipUnless(config.REAL_OLLAMA_TESTS, _SKIP_REASON)
class TestApiImageAnalysisSystem(ApiTestCase):

    def setUp(self):
        self.delete_all_user_data()

    def _upload_and_assert_analyzing(self, image_bytes, filename, content_type, location, include_explainability):
        response = self.upload_image(
            self.analysis_url("/upload"), image_bytes, location, filename, content_type, include_explainability
        )
        assert response.status_code == 200
        body = response.json()
        assert "analysis_id" in body
        assert body.get("status") == "analyzing"
        assert body.get("analysis_id") > 0
        return body

    def _wait_for_completed_analysis(self, analysis_id):
        analysis = self.wait_for_analysis_terminal_status(analysis_id)
        assert analysis is not None, f"Analysis {analysis_id} must appear in history before timeout"
        assert analysis.get("status") != "cancelled", (
            f"Analysis {analysis_id} unexpectedly cancelled - check the Ollama worker logs"
        )
        assert analysis.get("status") == "completed", f"Analysis {analysis_id} must complete successfully"
        return analysis

    def test_base_gallery_jpg_under_limit_without_explainability_completes_with_cloud_results(self):
        logger.debug("Starting the test: " + self._testMethodName)
        upload = self._upload_and_assert_analyzing(
            self.create_cloudy_jpeg(), "base-gallery.jpg", "image/jpeg", "Base Gallery City", False
        )
        completed = self._wait_for_completed_analysis(upload["analysis_id"])
        assert completed["results"]["cloudTypes"]
        logger.debug("Ending the test: " + self._testMethodName)

    def test_camera_origin_jpg_is_processed_like_gallery_upload(self):
        logger.debug("Starting the test: " + self._testMethodName)
        upload = self._upload_and_assert_analyzing(
            self.create_cloudy_jpeg(), "camera-capture.jpg", "image/jpeg", "Camera City", False
        )
        completed = self._wait_for_completed_analysis(upload["analysis_id"])
        assert completed.get("status") == "completed"
        logger.debug("Ending the test: " + self._testMethodName)

    def test_upload_with_no_selected_file_is_rejected(self):
        logger.debug("Starting the test: " + self._testMethodName)
        status = self.upload_without_file_status(self.analysis_url("/upload"), "No File City")
        assert status == 422
        logger.debug("Ending the test: " + self._testMethodName)

    def test_zero_byte_image_is_rejected(self):
        logger.debug("Starting the test: " + self._testMethodName)
        status = self.upload_image_status(
            self.analysis_url("/upload"), self.create_empty_image_bytes(), "Empty Image City",
            "empty.jpg", "image/jpeg", False
        )
        assert status == 400
        logger.debug("Ending the test: " + self._testMethodName)

    def test_image_larger_than_five_mb_is_rejected(self):
        logger.debug("Starting the test: " + self._testMethodName)
        status = self.upload_image_status(
            self.analysis_url("/upload"), self.create_too_large_payload(), "Too Large City",
            "too-large.jpg", "image/jpeg", False
        )
        assert status == 413
        logger.debug("Ending the test: " + self._testMethodName)

    def test_non_jpg_upload_is_rejected(self):
        logger.debug("Starting the test: " + self._testMethodName)
        status = self.upload_image_status(
            self.analysis_url("/upload"), self.create_non_jpeg_payload(), "Wrong Format City",
            "not-a-jpg.txt", "text/plain", False
        )
        assert status >= 400
        logger.debug("Ending the test: " + self._testMethodName)

    def test_explainability_with_clouds_completes_with_normalized_bounding_boxes(self):
        logger.debug("Starting the test: " + self._testMethodName)
        upload = self._upload_and_assert_analyzing(
            self.create_cloudy_jpeg(), "explainability-clouds.jpg", "image/jpeg", "Explainability City", True
        )
        completed = self._wait_for_completed_analysis(upload["analysis_id"])
        assert _has_normalized_box(completed["results"]["cloudDetails"])
        logger.debug("Ending the test: " + self._testMethodName)

    def test_no_cloud_jpg_without_explainability_completes_without_boxes(self):
        logger.debug("Starting the test: " + self._testMethodName)
        upload = self._upload_and_assert_analyzing(
            self.create_no_cloud_jpeg(), "clear-sky.jpg", "image/jpeg", "Clear Sky City", False
        )
        completed = self._wait_for_completed_analysis(upload["analysis_id"])
        results = completed["results"]
        assert _is_no_cloud_compatible(results)
        assert not _has_normalized_box(results["cloudDetails"])
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
