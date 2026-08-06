// Small DOM predicates shared by page objects that need to translate
// selenium-java's XPath "contains any of these keywords/labels" locators
// (LoginPage.LOGIN_FEEDBACK, RegisterPage.REGISTER_FEEDBACK, BasePage's
// hasInvalidRequiredInput) into plain jQuery/DOM checks.

/** True when the jQuery-wrapped body's text contains any of `keywords` (case-insensitive). */
export function bodyTextContainsAny($body, keywords) {
  const text = $body.text().toLowerCase();
  return keywords.some((keyword) => text.includes(keyword.toLowerCase()));
}

/** True when any `required` input currently fails native browser validation. */
export function hasInvalidRequiredInput(doc) {
  return Array.from(doc.querySelectorAll('input')).some((input) => input.required && !input.checkValidity());
}

/** Last element among `selector` whose text includes `text`, restricted to visible ones. */
export function lastVisibleContaining(selector, text) {
  return cy
    .get(selector)
    .filter((_, el) => Cypress.$(el).text().trim().includes(text))
    .filter(':visible')
    .last();
}
