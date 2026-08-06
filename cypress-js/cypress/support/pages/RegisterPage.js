import BasePage from './BasePage';
import LoginPage from './LoginPage';
import HomePage from './HomePage';
import { bodyTextContainsAny, hasInvalidRequiredInput } from '../common/domChecks';

const USERNAME_PLACEHOLDER = 'Nombre de usuario';
const EMAIL_PLACEHOLDER = 'Correo electrónico';
const PASSWORD_PLACEHOLDER = 'Contraseña';
const CONFIRM_PASSWORD_PLACEHOLDER = 'Confirmar contraseña';
const LOGIN_LINK_TEXT = 'Inicia sesión';
const HOME_MARKER_TEXT = 'Bienvenido';
const INTERACTIVE_SELECTOR = '[role="button"], button, [tabindex]';
const SUBMIT_KEYWORDS = ['registr', 'crear'];
const VERIFY_DIALOG_KEYWORDS = ['verific', 'correo'];
const REGISTER_FEEDBACK_KEYWORDS = [
  'error',
  'inválid',
  'invalid',
  'contraseña',
  'correo',
  'usuario',
  'coincid',
  'uso',
  'obligatorio',
  'requerid',
];

/**
 * Page Object for the Register form. Constructing this object waits until
 * the username input is visible.
 */
export default class RegisterPage extends BasePage {
  constructor() {
    super();
    this.byPlaceholder(USERNAME_PLACEHOLDER).should('be.visible');
  }

  // ── Assertions / queries ─────────────────────────────────────────────────

  assertUsernameInputVisible() {
    this.byPlaceholder(USERNAME_PLACEHOLDER).should('be.visible');
    return this;
  }

  assertEmailInputVisible() {
    this.byPlaceholder(EMAIL_PLACEHOLDER).should('be.visible');
    return this;
  }

  assertPasswordInputVisible() {
    this.byPlaceholder(PASSWORD_PLACEHOLDER).should('be.visible');
    return this;
  }

  assertConfirmPasswordInputVisible() {
    this.byPlaceholder(CONFIRM_PASSWORD_PLACEHOLDER).should('be.visible');
    return this;
  }

  assertLoginLinkVisible() {
    this.byPartialText(LOGIN_LINK_TEXT).should('be.visible');
    return this;
  }

  /** Yields (Cypress-chainable) true when the "verify your email" guidance is showing. */
  isVerificationDialogVisible() {
    return cy.get('body').then(($body) => {
      const text = $body.text().toLowerCase();
      return VERIFY_DIALOG_KEYWORDS.every((keyword) => text.includes(keyword));
    });
  }

  /** Yields (Cypress-chainable) true when a register error or validation feedback is showing. */
  hasRegisterErrorOrValidation() {
    return cy.get('body').then(($body) => {
      return bodyTextContainsAny($body, REGISTER_FEEDBACK_KEYWORDS) || hasInvalidRequiredInput($body[0].ownerDocument);
    });
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  enterUsername(username) {
    this.byPlaceholder(USERNAME_PLACEHOLDER).clear({ force: true }).type(username, { force: true });
    return this;
  }

  enterEmail(email) {
    this.byPlaceholder(EMAIL_PLACEHOLDER).clear({ force: true }).type(email, { force: true });
    return this;
  }

  enterPassword(password) {
    this.byPlaceholder(PASSWORD_PLACEHOLDER).clear({ force: true }).type(password, { force: true });
    return this;
  }

  enterConfirmPassword(password) {
    this.byPlaceholder(CONFIRM_PASSWORD_PLACEHOLDER).clear({ force: true }).type(password, { force: true });
    return this;
  }

  submitRegister() {
    cy.get('body').then(($body) => {
      const candidates = Cypress.$.makeArray($body.find(INTERACTIVE_SELECTOR)).filter((el) => {
        const text = el.textContent.trim().toLowerCase();
        return SUBMIT_KEYWORDS.some((keyword) => text.includes(keyword));
      });
      const visible = [...candidates].reverse().find((el) => Cypress.$(el).is(':visible'));
      cy.wrap(visible).click({ force: true });
    });
    return this;
  }

  register(username, email, password, confirmPassword) {
    this.enterUsername(username);
    this.enterEmail(email);
    this.enterPassword(password);
    this.enterConfirmPassword(confirmPassword);
    return this.submitRegister();
  }

  waitForHome() {
    this.byPartialText(HOME_MARKER_TEXT).should('be.visible');
    return new HomePage();
  }

  waitForVerificationDialog() {
    cy.get('body', { timeout: 30000 }).should(($body) => {
      const text = $body.text().toLowerCase();
      const shown = VERIFY_DIALOG_KEYWORDS.every((keyword) => text.includes(keyword));
      if (!shown) {
        throw new Error('Verification dialog did not appear before timeout');
      }
    });
    return this;
  }

  waitForRegisterFailure() {
    cy.get('body', { timeout: 30000 }).should(($body) => {
      const hasFailure =
        bodyTextContainsAny($body, REGISTER_FEEDBACK_KEYWORDS) || hasInvalidRequiredInput($body[0].ownerDocument);
      const usernamePresent = $body.find(`input[placeholder="${USERNAME_PLACEHOLDER}"]`).length > 0;
      if (!(hasFailure && usernamePresent)) {
        throw new Error('Registration was not rejected before timeout');
      }
    });
    return this;
  }

  /** Navigates back to the Login form. */
  clickLoginLink() {
    this.clickByText(LOGIN_LINK_TEXT);
    return new LoginPage();
  }
}
