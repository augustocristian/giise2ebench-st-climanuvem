# -*- coding: utf-8 -*-
"""API tests for the cancellation endpoint, mirroring selenium-java's
``TestApiCancel``:
  - PATCH /analysis/{id}/cancel — cancel an in-progress analysis
Runs with DISABLE_WORKER=true so uploaded analyses stay in 'analyzing'
status, making cancellation deterministic without Ollama.
"""
import logging
import unittest

from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)

NON_EXISTENT_ID = 2147483647  # Integer.MAX_VALUE, mirroring the Java fixture


class TestApiCancel(ApiTestCase):

    def test_cancel_analysis_returns_200(self):
        logger.debug("Starting the test: " + self._testMethodName)
        analysis_id = self.create_analysis("Cancel Me City")

        status = self.patch_status_auth(self.analysis_url(f"/{analysis_id}/cancel"))
        assert status == 200
        logger.debug("Ending the test: " + self._testMethodName)

    def test_cancel_already_cancelled_returns_400(self):
        logger.debug("Starting the test: " + self._testMethodName)
        analysis_id = self.create_analysis("Double Cancel City")

        self.patch_status_auth(self.analysis_url(f"/{analysis_id}/cancel"))
        second_status = self.patch_status_auth(self.analysis_url(f"/{analysis_id}/cancel"))
        assert second_status == 400
        logger.debug("Ending the test: " + self._testMethodName)

    def test_cancel_non_existent_analysis_returns_404(self):
        logger.debug("Starting the test: " + self._testMethodName)
        status = self.patch_status_auth(self.analysis_url(f"/{NON_EXISTENT_ID}/cancel"))
        assert status == 404
        logger.debug("Ending the test: " + self._testMethodName)

    def test_cancel_requires_auth(self):
        logger.debug("Starting the test: " + self._testMethodName)
        analysis_id = self.create_analysis("Auth Check City")
        status = self.get_status(self.analysis_url(f"/{analysis_id}/cancel"))
        assert status == 403
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
