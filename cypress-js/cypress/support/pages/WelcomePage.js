import BasePage from './BasePage';
import LoginPage from './LoginPage';
import HomePage from './HomePage';

const GUEST_BUTTON_TEXT = 'Continue as guest';
const LOGIN_BUTTON_TEXT = 'Log In';
const APP_TITLE_TEXT = 'ClimaNuvem';
const TAGLINE_TEXT = 'Pocket Meteorologist';

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

  /** Clicks "Log In" and waits for the Login form to appear. */
  clickLoginButton() {
    this.clickByTextUntil(LOGIN_BUTTON_TEXT, (doc) => doc.querySelector('input') !== null);
    return new LoginPage();
  }

  /**
   * Clicks "Continue as guest", which triggers Firebase anonymous auth,
   * and waits for the Home screen to mount.
   */
  clickAnonymousLogin() {
    this.clickByTextUntil(GUEST_BUTTON_TEXT, (doc) => doc.body.innerText.includes('Welcome!'));
    return new HomePage();
  }
}
