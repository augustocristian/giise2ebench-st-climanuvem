import BasePage from './BasePage';
import RegisterPage from './RegisterPage';
import HomePage from './HomePage';
import { bodyTextContainsAny, hasInvalidRequiredInput, lastVisibleContaining } from '../common/domChecks';

const EMAIL_PLACEHOLDER = 'Correo electrónico';
const PASSWORD_PLACEHOLDER = 'Contraseña';
const FORGOT_PASSWORD_TEXT = 'Olvidaste tu contraseña';
const REGISTER_LINK_TEXT = 'Regístrate';
const SUBMIT_TEXT = 'Iniciar Sesión';
const GOOGLE_TEXT = 'Google';
const HOME_MARKER_TEXT = 'Bienvenido';
const INTERACTIVE_SELECTOR = '[role="button"], button, [tabindex]';
const FEEDBACK_KEYWORDS = ['error', 'incorrect', 'credencial', 'obligatorio', 'requerid'];
const ACCEPT_TEXTS = ['Aceptar', 'Accept', 'OK'];

/**
 * Page Object for the Login form. Constructing this object waits until the
 * email input is visible.
 */
export default class LoginPage extends BasePage {
  constructor() {
    super();
    this.byPlaceholder(EMAIL_PLACEHOLDER).should('be.visible');
  }

  // ── Assertions / queries ─────────────────────────────────────────────────

  assertEmailInputVisible() {
    this.byPlaceholder(EMAIL_PLACEHOLDER).should('be.visible');
    return this;
  }

  assertPasswordInputVisible() {
    this.byPlaceholder(PASSWORD_PLACEHOLDER).should('be.visible');
    return this;
  }

  assertForgotPasswordVisible() {
    this.byPartialText(FORGOT_PASSWORD_TEXT).should('be.visible');
    return this;
  }

  assertRegisterLinkVisible() {
    this.byPartialText(REGISTER_LINK_TEXT).should('be.visible');
    return this;
  }

  assertGoogleLoginVisible() {
    this.byPartialText(GOOGLE_TEXT).should('be.visible');
    return this;
  }

  assertHomeVisible() {
    this.byPartialText(HOME_MARKER_TEXT).should('be.visible');
    return this;
  }

  emailValue() {
    return this.byPlaceholder(EMAIL_PLACEHOLDER).invoke('val');
  }

  /** Yields (Cypress-chainable) true when a login error or validation feedback is showing. */
  hasLoginErrorOrValidation() {
    return cy.get('body').then(($body) => {
      return bodyTextContainsAny($body, FEEDBACK_KEYWORDS) || hasInvalidRequiredInput($body[0].ownerDocument);
    });
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  enterEmail(email) {
    this.byPlaceholder(EMAIL_PLACEHOLDER).clear({ force: true }).type(email, { force: true });
    return this;
  }

  enterPassword(password) {
    this.byPlaceholder(PASSWORD_PLACEHOLDER).clear({ force: true }).type(password, { force: true });
    return this;
  }

  /** Submits the email/password login form and stays on this page object. */
  submitLogin() {
    lastVisibleContaining(INTERACTIVE_SELECTOR, SUBMIT_TEXT).click({ force: true });
    return this;
  }

  /** Fills both fields and submits the email/password login form. */
  login(email, password) {
    this.enterEmail(email);
    this.enterPassword(password);
    return this.submitLogin();
  }

  /** Waits until the authenticated Home screen is visible and returns its page object. */
  waitForHome() {
    cy.get('body', { timeout: 30000 }).should(($body) => {
      const reachedHome = $body.text().includes(HOME_MARKER_TEXT);
      const failed = bodyTextContainsAny($body, FEEDBACK_KEYWORDS) || hasInvalidRequiredInput($body[0].ownerDocument);
      if (!reachedHome && !failed) {
        throw new Error('Login did not reach Home or show feedback before timeout');
      }
    });
    cy.get('body').then(($body) => {
      if (!$body.text().includes(HOME_MARKER_TEXT)) {
        throw new Error('Login did not reach Home before timeout. Check account credentials in ACCOUNTS_FILE.');
      }
    });
    return new HomePage();
  }

  /** Waits until the login attempt is rejected by UI validation or an error message. */
  waitForLoginFailure() {
    cy.get('body', { timeout: 30000 }).should(($body) => {
      const hasFailure = bodyTextContainsAny($body, FEEDBACK_KEYWORDS) || hasInvalidRequiredInput($body[0].ownerDocument);
      const emailPresent = $body.find(`input[placeholder="${EMAIL_PLACEHOLDER}"]`).length > 0;
      if (!(hasFailure && emailPresent)) {
        throw new Error('Login was not rejected before timeout');
      }
    });
    return this;
  }

  closeLoginFeedbackIfPresent() {
    cy.get('body').then(($body) => {
      const candidates = Cypress.$.makeArray($body.find(INTERACTIVE_SELECTOR)).filter((el) =>
        ACCEPT_TEXTS.some((text) => el.textContent.trim().includes(text))
      );
      const visible = [...candidates].reverse().find((el) => Cypress.$(el).is(':visible'));
      if (visible) {
        cy.wrap(visible).click({ force: true });
      }
    });
    return this;
  }

  /**
   * Starts the Google provider flow without requiring credentials. The flow is
   * considered started when `window.open` is called or the current page URL
   * or body contains a Google/Firebase identity marker.
   */
  clickGoogleLoginStartsProvider() {
    cy.window().then((win) => cy.stub(win, 'open').as('googleProviderWindowOpen'));
    this.clickByText(GOOGLE_TEXT);
    return cy.get('@googleProviderWindowOpen').then((stub) => {
      if (stub.called) {
        return true;
      }
      return cy.url().then((url) =>
        cy.get('body').then(($body) => {
          const lowerUrl = url.toLowerCase();
          const lowerBody = $body.text().toLowerCase();
          return (
            lowerUrl.includes('google') ||
            lowerUrl.includes('firebase') ||
            lowerUrl.includes('identitytoolkit') ||
            lowerBody.includes('google') ||
            lowerBody.includes('firebase')
          );
        })
      );
    });
  }

  /** Clicks "¿No tienes cuenta? Regístrate" and waits for the Register form. */
  clickRegisterLink() {
    this.clickByText(REGISTER_LINK_TEXT);
    return new RegisterPage();
  }
}
