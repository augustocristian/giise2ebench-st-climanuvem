import BasePage from './BasePage';
import LoginPage from './LoginPage';
import HomePage from './HomePage';

const GUEST_BUTTON_TEXT = 'Continuar como invitado';
const LOGIN_BUTTON_TEXT = 'Iniciar Sesión';
const APP_TITLE_TEXT = 'ClimaNuvem';
const TAGLINE_TEXT = 'Meteorólogo de bolsillo';

/**
 * Page Object for the Welcome (root) screen — the first page any visitor sees.
 * Constructing this object waits until the guest-login button is visible,
 * guaranteeing the app has fully mounted before any assertion runs.
 */
export default class WelcomePage extends BasePage {
  constructor() {
    super();
    this.byPartialText(GUEST_BUTTON_TEXT).should('be.visible');
  }

  // ── Assertions ────────────────────────────────────────────────────────────

  assertAppTitleVisible() {
    this.byPartialText(APP_TITLE_TEXT).should('be.visible');
    return this;
  }

  assertTaglineVisible() {
    this.byPartialText(TAGLINE_TEXT).should('be.visible');
    return this;
  }

  assertLoginButtonVisible() {
    this.byPartialText(LOGIN_BUTTON_TEXT).should('be.visible');
    return this;
  }

  assertGuestButtonVisible() {
    this.byPartialText(GUEST_BUTTON_TEXT).should('be.visible');
    return this;
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /** Clicks "Iniciar Sesión" and waits for the Login form to appear. */
  clickLoginButton() {
    this.clickByText(LOGIN_BUTTON_TEXT);
    return new LoginPage();
  }

  /**
   * Clicks "Continuar como invitado", which triggers Firebase anonymous auth,
   * and waits for the Home screen to mount.
   */
  clickAnonymousLogin() {
    this.clickByText(GUEST_BUTTON_TEXT);
    return new HomePage();
  }
}
