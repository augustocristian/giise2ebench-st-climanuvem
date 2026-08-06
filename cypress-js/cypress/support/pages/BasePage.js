// Base for every Page Object screen class — one per SUT screen, same split as
// selenium-java's pages/BasePage.java. Cypress's cy.get()/cy.contains() are
// retry-and-wait-until-actionable by default, so the WebDriverWait +
// JS-dispatched-click plumbing that Selenium needed is not reproduced here;
// {force: true} stands in for it on the rare React Native Web element that
// sits outside a real click box.
export default class BasePage {
  /** Deepest element whose text contains `text` — cy.contains()'s default semantics. */
  byPartialText(text) {
    return cy.contains(text);
  }

  /** `<input>` located by its placeholder attribute. */
  byPlaceholder(placeholder) {
    // Stack navigation keeps previous screens mounted (hidden), so only visible inputs count.
    return cy.get(`input[placeholder="${placeholder}"]`).filter(':visible');
  }

  /** Clicks the element found by partial text; returns `this` for chaining. */
  clickByText(text) {
    this.byPartialText(text).scrollIntoView().click({ force: true });
    return this;
  }

  /**
   * Clicks the element found by partial text and retries the click until `isNextScreen(document)`
   * is true. On first load the app can render a button before its press handlers are attached, so
   * a single forced click may be silently lost.
   */
  clickByTextUntil(text, isNextScreen, { attempts = 4, probeMs = 2500 } = {}) {
    const attempt = (remaining) => {
      this.clickByText(text);
      cy.window({ log: false })
        .then((win) => new Cypress.Promise((resolve) => {
          const started = Date.now();
          const timer = setInterval(() => {
            const reached = isNextScreen(win.document);
            if (reached || Date.now() - started > probeMs) {
              clearInterval(timer);
              resolve(reached);
            }
          }, 100);
        }))
        .then((reached) => {
          if (!reached && remaining > 1) {
            attempt(remaining - 1);
          }
        });
    };
    attempt(attempts);
    return this;
  }

  /** Clears and types into the input located by placeholder; returns `this`. */
  fillByPlaceholder(placeholder, text) {
    this.replaceText(this.byPlaceholder(placeholder), text);
    return this;
  }

  /** Clears an input and types `text` (cy.type() rejects an empty string, so an empty value only clears). */
  replaceText(chain, text) {
    const cleared = chain.clear({ force: true });
    if (text !== '') {
      cleared.type(text, { force: true });
    }
    return this;
  }

  /** Last *visible* element among all matches of `selector` (mirrors "last visible submit button"). */
  lastVisible(selector) {
    return cy.get(selector).filter(':visible').last();
  }
}
