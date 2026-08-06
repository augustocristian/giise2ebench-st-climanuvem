# -*- coding: utf-8 -*-
"""API tests for the public health-check endpoints that require no
authentication, mirroring selenium-java's ``TestApiPing``:
  - GET /ping  — liveness probe
  - GET /      — service status response
"""
import logging
import unittest

from climanuvem.common.api_client import ApiTestCase

logger = logging.getLogger(__name__)


class TestApiPing(ApiTestCase):

    def test_ping_endpoint(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status(self.root_url("/ping")) == 200

        body = self.get_json(self.root_url("/ping"))
        assert body.get("ping") == "pong"
        logger.debug("Ending the test: " + self._testMethodName)

    def test_root_endpoint(self):
        logger.debug("Starting the test: " + self._testMethodName)
        assert self.get_status(self.root_url("/")) == 200

        body = self.get_json(self.root_url("/"))
        assert body.get("service") == "ClimaNuvem API"
        assert body.get("status") == "ok"
        logger.debug("Ending the test: " + self._testMethodName)


if __name__ == '__main__':
    unittest.main()
