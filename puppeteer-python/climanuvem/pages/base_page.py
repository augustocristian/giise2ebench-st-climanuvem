# -*- coding: utf-8 -*-
"""Abstract base for all Page Objects. Mirrors selenium-java's
``BasePage``: centralises the page handle and the primitives every page
needs — :meth:`is_present`, :meth:`click`, and :meth:`fill` — plus shared
locator factories. Subclasses declare their own locators as class-level
constants and expose typed, readable methods that either return a
bool/value or the next page.

Pyppeteer's ``waitForXPath``/``waitForSelector`` with ``visible=True``
already wait-and-return the first visible match, so there is no need for
the JS-dispatched-click plumbing Selenium's WebDriver required — a real
``ElementHandle.click()`` performs a trusted-enough mouse click that React
Native Web's event handlers pick up natively.
"""
import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

TIMEOUT_MS = 30_000

Locator = namedtuple("Locator", ["kind", "value"])


class BasePage:
    def __init__(self, session):
        self._session = session
        self._page = session.page

    def _run(self, coro):
        return self._session.run(coro)

    # ── Shared locator factories ────────────────────────────────────────

    @staticmethod
    def by_text(text: str) -> Locator:
        """XPath: any element whose full text equals `text` (innermost match only)."""
        escaped = text.replace("'", "\\'")
        return Locator("xpath", f"//*[normalize-space(.)='{escaped}' and not(.//*[normalize-space(.)='{escaped}'])]")

    @staticmethod
    def by_partial_text(text: str) -> Locator:
        """XPath: any element whose text contains `text` as a substring (innermost match only)."""
        escaped = text.replace("'", "\\'")
        return Locator(
            "xpath",
            f"//*[contains(normalize-space(.),'{escaped}') and not(.//*[contains(normalize-space(.),'{escaped}')])]",
        )

    @staticmethod
    def by_xpath(expression: str) -> Locator:
        return Locator("xpath", expression)

    @staticmethod
    def input_by_placeholder(placeholder: str) -> Locator:
        """CSS: <input> with the given placeholder."""
        return Locator("css", f'input[placeholder="{placeholder}"]')

    # ── Element lookup ───────────────────────────────────────────────────

    def _find_all(self, locator: Locator):
        if locator.kind == "xpath":
            return self._run(self._page.xpath(locator.value))
        return self._run(self._page.querySelectorAll(locator.value))

    def _last_visible(self, elements, required: bool):
        target = None
        for element in elements:
            if self._run(element.boundingBox()) is not None:
                target = element
        if target is None and required:
            raise AssertionError("No visible element found among matches")
        return target

    # ── Queries ──────────────────────────────────────────────────────────

    def is_present(self, locator: Locator) -> bool:
        """True when at least one element matching `locator` exists in the DOM."""
        return len(self._find_all(locator)) > 0

    def is_visible(self, locator: Locator) -> bool:
        """True when any element matching `locator` is currently visible."""
        return self._last_visible(self._find_all(locator), required=False) is not None

    def input_value(self, locator: Locator) -> str:
        """Returns the current `value` attribute of the (first) matching input element."""
        element = self._find_all(locator)[0]
        return self._run(self._page.evaluate("el => el.value", element))

    def has_invalid_required_input(self) -> bool:
        """True when any required input currently fails browser-side validation."""
        script = (
            "() => Array.from(document.querySelectorAll('input'))"
            ".filter(el => el.required && !el.checkValidity()).length"
        )
        return self._run(self._page.evaluate(script)) > 0

    def body_text_contains_any(self, keywords) -> bool:
        text = self._run(self._page.evaluate("() => document.body.innerText")).lower()
        return any(keyword.lower() in text for keyword in keywords)

    # ── Actions ──────────────────────────────────────────────────────────

    def wait_for(self, locator: Locator, timeout: int = TIMEOUT_MS):
        """Waits for `locator` to be visible and returns its ElementHandle."""
        options = {"visible": True, "timeout": timeout}
        if locator.kind == "xpath":
            return self._run(self._page.waitForXPath(locator.value, options))
        return self._run(self._page.waitForSelector(locator.value, options))

    def click(self, locator: Locator) -> None:
        """Waits for `locator` to be visible and clicks it (first visible match)."""
        element = self.wait_for(locator)
        self._run(element.click())

    def click_last_visible(self, locator: Locator) -> None:
        """Waits for `locator`, then clicks the *last* visible match among all of them —
        used where React Native Web renders multiple candidates and only the last one is
        the "real" interactive one (e.g. submit buttons, duplicated "Sistema" options)."""
        self.wait_for(locator)
        target = self._last_visible(self._find_all(locator), required=True)
        self._run(target.click())

    def fill(self, locator: Locator, text: str) -> None:
        """Waits for `locator`, clears it, and types `text`."""
        element = self.wait_for(locator)
        self._run(element.click())
        self._run(self._page.keyboard.down("Control"))
        self._run(self._page.keyboard.press("KeyA"))
        self._run(self._page.keyboard.up("Control"))
        self._run(self._page.keyboard.press("Backspace"))
        self._run(element.type(text))
