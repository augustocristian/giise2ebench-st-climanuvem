"""Fixtures of the API tests: one HTTP client against the SUT for the whole session."""
from collections.abc import Iterator

import pytest

from climanuvem.common import ApiClient


@pytest.fixture(scope="session")
def api() -> Iterator[ApiClient]:
    client = ApiClient()
    yield client
    client.close()


@pytest.fixture
def empty_history(api: ApiClient) -> None:
    """Gives the test an empty history regardless of earlier runs."""
    api.delete_all_analyses()
