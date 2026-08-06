import BasePage from './BasePage';
import { bodyTextContainsAny } from '../common/domChecks';

const INTERACTIVE_SELECTOR = '[role="button"], button, [tabindex]';

const PROFILE_TITLE = /My Profile/;
const GUEST_PREFS = /Guest preferences/;
const USERNAME_SECTION = /Username/;
const USERNAME_INPUT_SELECTOR = 'input[placeholder="Enter your name"]';

const STATUS_FEEDBACK_KEYWORDS = [
  'perfil actualizado',
  'profile updated',
  'fallo de seguridad',
  'security failure',
  'error al eliminar datos',
  'error deleting data',
  'nombre de usuario debe tener',
  'username must be between',
];

/** Page Object for profile configuration — mirrors both guest and authenticated states. */
export default class ProfilePage extends BasePage {
  constructor() {
    super();
    this.byAnyText(PROFILE_TITLE).should('be.visible');
  }

  // ── Locator helpers ──────────────────────────────────────────────────────

  /** Element (any tag) whose text matches the given regex — mirrors ProfilePage.anyText. */
  byAnyText(regex) {
    return cy.contains(regex);
  }

  /** Interactive element whose text matches the given regex — mirrors ProfilePage.anyInteractiveText. */
  byAnyInteractiveText(regex) {
    return cy.contains(INTERACTIVE_SELECTOR, regex);
  }

  usernameInput() {
    return cy.get(USERNAME_INPUT_SELECTOR).filter(':visible');
  }

  saveButton() {
    return this.byAnyInteractiveText(/Save Changes/);
  }

  statusFeedback() {
    return cy.get('body');
  }

  // ── Assertions / queries ─────────────────────────────────────────────────

  assertGuestPreferencesVisible() {
    this.byAnyText(GUEST_PREFS).should('be.visible');
    return this;
  }

  waitForGuestProfile() {
    this.byAnyText(GUEST_PREFS).should('be.visible');
    return this;
  }

  assertUsernameSectionVisible() {
    this.byAnyText(USERNAME_SECTION).should('be.visible');
    return this;
  }

  assertDeleteAccountVisible() {
    this.byAnyInteractiveText(/Delete Account/).should('be.visible');
    return this;
  }

  waitForAuthenticatedProfile() {
    this.byAnyText(USERNAME_SECTION).should('be.visible');
    this.byAnyInteractiveText(/Delete Account/).should('be.visible');
    return this;
  }

  assertDeleteConfirmVisible() {
    this.byAnyInteractiveText(/Yes, delete/).should('be.visible');
    return this;
  }

  assertDeleteConfirmGone() {
    cy.contains(INTERACTIVE_SELECTOR, /Yes, delete/).should('not.exist');
    return this;
  }

  currentUsername() {
    return this.usernameInput().invoke('val');
  }

  /** Yields (Cypress-chainable) true when the Save action is enabled. */
  isSaveButtonEnabled() {
    return this.saveButton().then(($button) => {
      const target = $button.closest('[role="button"],button,[tabindex]').get(0) || $button.get(0);
      return cy.window().then((win) => {
        const disabled =
          target.getAttribute('aria-disabled') === 'true' ||
          target.disabled === true ||
          win.getComputedStyle(target).pointerEvents === 'none';
        return !disabled;
      });
    });
  }

  hasStoredTheme(value) {
    return this.storedValue('appTheme').then((stored) => stored === value);
  }

  hasStoredLanguage(value) {
    return this.storedValue('appLanguage').then((stored) => stored === value);
  }

  storedValue(key) {
    return cy.window().then((win) => win.localStorage.getItem(key));
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  chooseLightTheme() {
    return this.chooseTheme('Light', 'light');
  }

  chooseDarkTheme() {
    return this.chooseTheme('Dark', 'dark');
  }

  chooseSystemTheme() {
    this.selectOption('System', { last: false });
    this.waitForStoredValue('appTheme', 'system');
    return this;
  }

  chooseEnglishLanguage() {
    this.selectOption('English', { last: false });
    this.waitForStoredValue('appLanguage', 'en');
    return this;
  }

  chooseSpanishLanguage() {
    this.selectOption('Spanish', { last: false });
    this.waitForStoredValue('appLanguage', 'es');
    return this;
  }

  chooseSystemLanguage() {
    // The UI is Spanish at this point (the previous step selected it), so the option reads "Sistema".
    this.selectOption(['System', 'Sistema'], { last: true });
    this.waitForStoredValue('appLanguage', 'system');
    return this;
  }

  setUsername(username) {
    this.replaceText(this.usernameInput(), username);
    return this;
  }

  updateUsername(username) {
    this.setUsername(username);
    this.saveButton().click({ force: true });
    return this;
  }

  waitForProfileFeedback() {
    cy.get('body', { timeout: 30000 }).should(($body) => {
      if (!bodyTextContainsAny($body, STATUS_FEEDBACK_KEYWORDS)) {
        throw new Error('Profile feedback did not appear before timeout');
      }
    });
    return this;
  }

  closeProfileFeedback() {
    cy.contains(INTERACTIVE_SELECTOR, /Accept|OK/).click({ force: true });
    cy.get('body').should(($body) => {
      if (bodyTextContainsAny($body, STATUS_FEEDBACK_KEYWORDS)) {
        throw new Error('Profile feedback did not close');
      }
    });
    return this;
  }

  openDeleteAccountDialog() {
    cy.get(INTERACTIVE_SELECTOR)
      .filter((_, el) => /Delete Account/.test(el.textContent))
      .filter(':visible')
      .last()
      .click({ force: true });
    this.assertDeleteConfirmVisible();
    return this;
  }

  cancelDeleteAccount() {
    this.byAnyInteractiveText(/Cancel/).click({ force: true });
    this.assertDeleteConfirmGone();
    return this;
  }

  // ── Internals ────────────────────────────────────────────────────────────

  chooseTheme(text, storedValue) {
    this.selectOption(text, { last: false });
    this.waitForStoredValue('appTheme', storedValue);
    return this;
  }

  /**
   * Clicks the first (or last, when `last: true`) *visible* interactive
   * element matching `text`. "System" appears once
   * under theme options and once under language options — `last` picks
   * between them, mirroring ProfilePage.clickOption's `lastMatch` flag.
   */
  selectOption(text, { last = false } = {}) {
    const labels = [].concat(text);
    cy.get('body').then(($body) => {
      // Deepest visible element whose whole text is one of the labels.
      const matches = [...$body.find('*')].filter((el) =>
        labels.includes(el.textContent.trim())
        && Cypress.$(el).is(':visible')
        && ![...el.children].some((child) => labels.includes(child.textContent.trim())));
      const target = last ? matches.at(-1) : matches[0];
      cy.wrap(target).click({ force: true });
    });
    return this;
  }

  waitForStoredValue(key, expectedValue) {
    cy.window()
      .its('localStorage')
      .invoke('getItem', key)
      .should('eq', expectedValue);
    return this;
  }
}
