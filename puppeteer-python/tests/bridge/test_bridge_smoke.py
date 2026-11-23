"""Smoke test of the Python-Node Puppeteer bridge.

It drives a tiny page served from a local HTTP server, so it needs Chrome and Node but not the SUT.
"""
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from climanuvem.browser import Browser, BridgeProtocolError, ElementTimeoutError, Page, TestId

FORM = TestId.of("demo-form")
NAME = TestId.of("demo-name")
PASSWORD = TestId.of("demo-password")
TOGGLE = TestId.of("demo-toggle")
SUBMIT = TestId.of("demo-submit")
ERROR = TestId.of("demo-error")
MISSING = TestId.of("does-not-exist")

DEMO_PAGE = b"""<!doctype html>
<html><head><title>Bridge demo</title></head>
<body>
  <form data-testid="demo-form">
    <input data-testid="demo-name" type="text">
    <input data-testid="demo-password" type="password">
    <button type="button" data-testid="demo-toggle">Show</button>
    <button type="submit" data-testid="demo-submit">Send</button>
    <p data-testid="demo-error" hidden>Invalid credentials</p>
  </form>
  <script>
    const form = document.querySelector("form");
    const password = form.querySelector("[data-testid=demo-password]");
    form.querySelector("[data-testid=demo-toggle]").onclick = () => {
      password.type = password.type === "password" ? "text" : "password";
    };
    form.onsubmit = (event) => {
      event.preventDefault();
      form.querySelector("[data-testid=demo-error]").hidden = false;
    };
  </script>
</body></html>"""


class _DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - name required by BaseHTTPRequestHandler
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(DEMO_PAGE)))
        self.end_headers()
        self.wfile.write(DEMO_PAGE)

    def log_message(self, format: str, *args: object) -> None:
        """Keeps the test output clean."""


@pytest.fixture(scope="module")
def demo_url() -> Iterator[str]:
    server = HTTPServer(("127.0.0.1", 0), _DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
async def demo(page: Page, demo_url: str) -> Page:
    await page.goto(demo_url)
    await page.locator(FORM).wait_for("visible")
    return page


async def test_finds_form_and_reads_state(demo: Page, demo_url: str):
    assert await demo.url() == demo_url
    assert await demo.title() == "Bridge demo"
    assert await demo.locator(FORM).count() == 1
    assert await demo.locator(FORM).is_visible()
    assert await demo.locator(SUBMIT).is_enabled()
    assert await demo.locator(PASSWORD).attribute("type") == "password"
    assert await demo.locator(PASSWORD).property("disabled") is False
    assert await demo.locator(ERROR).count() == 1
    assert not await demo.locator(ERROR).is_visible()
    assert await demo.locator(MISSING).count() == 0
    assert not await demo.locator(MISSING).is_visible()


async def test_fill_type_and_clear(demo: Page):
    name = demo.locator(NAME)
    await name.fill("someone@example.test")
    assert await name.input_value() == "someone@example.test"
    await name.fill("")
    assert await name.input_value() == ""
    await name.fill("overwritten")
    await name.fill("short")
    assert await name.input_value() == "short"
    await name.fill("")
    await name.type("abc", delay_ms=10)
    assert await name.input_value() == "abc"


async def test_click_toggles_and_submit_shows_error(demo: Page):
    await demo.locator(TOGGLE).click()
    assert await demo.locator(PASSWORD).attribute("type") == "text"
    await demo.locator(ERROR).wait_for("hidden")
    await demo.locator(SUBMIT).click()
    await demo.locator(ERROR).wait_for("visible")
    assert await demo.locator(ERROR).text() == "Invalid credentials"


async def test_press_enter_submits_form(demo: Page):
    await demo.locator(NAME).fill("someone")
    await demo.locator(PASSWORD).press("Enter")
    await demo.locator(ERROR).wait_for("visible")


async def test_press_key_acts_on_the_focused_element(demo: Page):
    await demo.locator(PASSWORD).click()
    await demo.press_key("Enter")
    await demo.locator(ERROR).wait_for("visible")


async def test_wait_for_states(demo: Page):
    await demo.locator(FORM).wait_for("attached")
    await demo.locator(MISSING).wait_for("hidden")
    await demo.locator(MISSING).wait_for("detached")
    await demo.evaluate("() => document.querySelector('[data-testid=\"demo-form\"]').remove()")
    await demo.locator(FORM).wait_for("detached")
    await demo.locator(FORM).wait_for("hidden")


async def test_evaluate_with_args_and_promises(demo: Page):
    assert await demo.evaluate("(a, b) => a + b", 2, 3) == 5
    greet = "async (name) => { await Promise.resolve(); return `hi ${name}`; }"
    assert await demo.evaluate(greet, "bridge") == "hi bridge"
    assert await demo.evaluate("() => location.pathname") == "/"


async def test_init_script_runs_before_page_scripts(page: Page, demo_url: str):
    await page.add_init_script("(value) => { window.__injected = value; }", "from-init-script")
    await page.goto(demo_url)
    assert await page.evaluate("() => window.__injected") == "from-init-script"
    await page.reload()
    assert await page.evaluate("() => window.__injected") == "from-init-script"


async def test_contexts_are_isolated(browser: Browser, demo_url: str):
    first = await browser.new_page()
    second = await browser.new_page()
    try:
        await first.goto(demo_url)
        await second.goto(demo_url)
        await first.evaluate("() => { localStorage.setItem('k', 'v'); document.cookie = 'c=1'; }")
        assert await first.evaluate("() => localStorage.getItem('k')") == "v"
        assert await second.evaluate("() => localStorage.getItem('k')") is None
        assert any(cookie["name"] == "c" for cookie in await first.cookies())
        assert await second.cookies() == []
        await first.clear_storage()
        await first.clear_cookies()
        assert await first.evaluate("() => localStorage.getItem('k')") is None
        assert await first.cookies() == []
    finally:
        await first.close()
        await second.close()


async def test_nth_and_within_scoping(demo: Page):
    inputs = demo.locator(FORM).within("input")
    assert await inputs.count() == 2
    assert await inputs.nth(0).attribute("data-testid") == "demo-name"
    assert await inputs.nth(1).attribute("data-testid") == "demo-password"
    assert await inputs.last().attribute("data-testid") == "demo-password"
    assert await demo.locator("input").nth(1).attribute("data-testid") == "demo-password"
    await inputs.first().fill("scoped")
    assert await demo.locator(NAME).input_value() == "scoped"
    assert await demo.locator(FORM).within(PASSWORD).count() == 1
    assert await inputs.nth(99).count() == 0


async def test_hover_scroll_screenshot_viewport_and_diagnostics(demo: Page, tmp_path):
    await demo.set_viewport(400, 600)
    assert await demo.evaluate("() => window.innerWidth") == 400
    await demo.locator(SUBMIT).hover()
    await demo.locator(SUBMIT).scroll_into_view()
    shot = await demo.screenshot(tmp_path / "shots" / "demo.png")
    assert shot.is_file() and shot.stat().st_size > 0
    await demo.evaluate("() => console.error('bridge-diagnostic-probe')")
    entries = await demo.diagnostics()
    assert any("bridge-diagnostic-probe" in entry["text"] for entry in entries)
    assert await demo.diagnostics() == []


async def test_timeout_and_protocol_error_paths(demo: Page):
    missing = demo.locator(MISSING, timeout_ms=500)
    with pytest.raises(ElementTimeoutError):
        await missing.click()
    with pytest.raises(ElementTimeoutError):
        await missing.wait_for("visible")
    with pytest.raises(ElementTimeoutError):
        await demo.locator(FORM).with_timeout(500).wait_for("hidden")
    with pytest.raises(BridgeProtocolError):
        await demo.evaluate("() => { throw new Error('boom'); }")
    with pytest.raises(BridgeProtocolError):
        await demo.locator("###").with_timeout(500).count()
