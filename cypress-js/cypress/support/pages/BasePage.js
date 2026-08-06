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
    return cy.get(`input[placeholder="${placeholder}"]`);
  }

  /** Clicks the element found by partial text; returns `this` for chaining. */
  clickByText(text) {
    this.byPartialText(text).scrollIntoView().click({ force: true });
    return this;
  }

  /** Clears and types into the input located by placeholder; returns `this`. */
  fillByPlaceholder(placeholder, text) {
    this.byPlaceholder(placeholder).clear({ force: true }).type(text, { force: true });
    return this;
  }

  /** Last *visible* element among all matches of `selector` (mirrors "last visible submit button"). */
  lastVisible(selector) {
    return cy.get(selector).filter(':visible').last();
  }
}
