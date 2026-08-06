# -*- coding: utf-8 -*-
"""API tests for the deletion endpoints, mirroring selenium-java's
``TestApiDelete``:
  - DELETE /analysis/{id}       — remove a single analysis (HTTP 200 or 404)
  - DELETE /analysis/user-data  — remove all analyses for the user (HTTP 200)
"""
import logging
import unittest

from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)

NON_EXISTENT_ID = 2147483647  # Integer.MAX_VALUE, mirroring the Java fixture


class TestApiDelete(ApiTestCase):

    def test_delete_single_analysis_returns_200(self):
        logger.debug("Starting the test: " + self._testMethodName)
        analysis_id = self.create_analysis("Delete Me City")

        status = self.delete_status_auth(self.analysis_url(f"/{analysis_id}"))
        assert status == 200

        history = self.get_json_auth(self.analysis_url("/history"))
        assert not self.contains_by_field(history, "id", analysis_id)
        logger.debug("Ending the test: " + self._testMethodName)

    def test_delete_non_existent_analysis_returns_404(self):
        logger.debug("Starting the test: " + self._testMethodName)
        status = self.delete_status_auth(self.analysis_url(f"/{NON_EXISTENT_ID}"))
        assert status == 404
        logger.debug("Ending the test: " + self._testMethodName)

    def test_delete_user_data_clears_history(self):
        logger.debug("Starting the test: " + self._testMethodName)
        self.create_analysis("Bulk Delete A")
        self.create_analysis("Bulk Delete B")

        status = self.delete_all_user_data()
        assert status == 200

        history = self.get_json_auth(self.analysis_url("/history"))
        assert history == []
        logger.debug("Ending the test: " + self._testMethodName)

    def test_delete_user_data_when_empty_returns_200(self):
        logger.debug("Starting the test: " + self._testMethodName)
        self.delete_all_user_data()
        status = self.delete_all_user_data()
        assert status == 200
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
