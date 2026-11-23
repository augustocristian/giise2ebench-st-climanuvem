"""Shared fixtures: a session-wide Chrome and one isolated page per browser test."""
import logging
import os
import re
from pathlib import Path

import pytest
import pytest_asyncio

from climanuvem.browser import Browser, Page
from climanuvem.common import config

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "reports" / "screenshots"


def pytest_collection_modifyitems(items):
    """Tags tests with the ``api``/``e2e``/``bridge`` markers from their folder."""
    for item in items:
        for marker in ("api", "e2e", "bridge"):
            if f"{os.sep}{marker}{os.sep}" in str(item.path):
                item.add_marker(marker)
                break


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """Exposes each phase's report so fixtures can react to a failed test."""
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return config.FRONTEND_URL


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def browser():
    """One Chrome for the whole session."""
    instance = await Browser.launch(
        headless=not config.HEADED,
        executable_path=config.BROWSER_EXECUTABLE_PATH,
        args=config.BROWSER_ARGS,
    )
    yield instance
    await instance.close()


@pytest_asyncio.fixture(loop_scope="session")
async def page(request, browser: Browser):
    """A page in its own isolated context, discarded after each test."""
    current: Page = await browser.new_page()
    yield current
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        await _save_failure_artifacts(request.node.name, current)
    await current.close()


async def _save_failure_artifacts(test_name: str, current: Page) -> None:
    safe_name = re.sub(r"[^\w.-]+", "_", test_name)
    try:
        path = await current.screenshot(SCREENSHOT_DIR / f"{safe_name}.png")
        logger.error("Screenshot of the failed test saved to %s", path)
        for entry in await current.diagnostics():
            logger.error("Browser diagnostic: %s", entry)
    except Exception as error:  # diagnostics must never mask the real failure
        logger.warning("Could not capture failure artifacts: %s", error)
