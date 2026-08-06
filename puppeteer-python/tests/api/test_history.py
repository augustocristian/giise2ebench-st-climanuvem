# -*- coding: utf-8 -*-
"""API tests for the analysis history endpoint, mirroring selenium-java's
``TestApiHistory``:
  - GET /analysis/history — returns all analyses for the authenticated user
A setUp cleanup ensures the test user starts with an empty history, making
each scenario deterministic regardless of prior test runs.
"""
import logging
import unittest

from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)


class TestApiHistory(ApiTestCase):

    def setUp(self):
        self.delete_all_user_data()

    def test_history_initially_empty(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status_auth(self.analysis_url("/history")) == 200

        history = self.get_json_auth(self.analysis_url("/history"))
        assert history == []
        logger.debug("Ending the test: " + self._testMethodName)

    def test_history_after_upload_contains_entry(self):
        logger.debug("Starting the test: " + self._testMethodName)
        analysis_id = self.create_analysis("Oviedo, Spain")

        history = self.get_json_auth(self.analysis_url("/history"))
        assert history
        assert self.contains_by_field(history, "id", analysis_id)
        logger.debug("Ending the test: " + self._testMethodName)

    def test_history_entry_has_required_fields(self):
        logger.debug("Starting the test: " + self._testMethodName)
        self.create_analysis("Test City")

        history = self.get_json_auth(self.analysis_url("/history"))
        assert history
        entry = history[0]
        for field in ("id", "status", "date", "location", "imageUrl", "results"):
            assert field in entry
        logger.debug("Ending the test: " + self._testMethodName)

    def test_history_results_block_has_required_fields(self):
        logger.debug("Starting the test: " + self._testMethodName)
        self.create_analysis("Results Field City")

        history = self.get_json_auth(self.analysis_url("/history"))
        assert history
        results = history[0]["results"]
        for field in ("cloudTypes", "cloudDetails", "forecast", "warnings"):
            assert field in results
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
