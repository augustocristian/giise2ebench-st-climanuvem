import BasePage from './BasePage';
import CapturePage from './CapturePage';
import ProfilePage from './ProfilePage';
import WelcomePage from './WelcomePage';

const WELCOME_MESSAGE_TEXT = 'Welcome!';
const ANALYZE_CARD_TEXT = 'Analyze Image';
const HISTORY_CARD_TEXT = 'History';
const LOGOUT_CARD_TEXT = 'Log Out';

/**
 * Page Object for the Home screen — shown after a successful login.
 * Constructing this object waits until both the welcome message and the
 * "Analyze Image" quick-action card are visible.
 */
export default class HomePage extends BasePage {
  constructor() {
    super();
    this.byPartialText(WELCOME_MESSAGE_TEXT).should('be.visible');
    this.byPartialText(ANALYZE_CARD_TEXT).should('be.visible');
  }

  // ── Assertions ────────────────────────────────────────────────────────────

  assertWelcomeMessageVisible() {
    this.byPartialText(WELCOME_MESSAGE_TEXT).should('be.visible');
    return this;
  }

  assertAnalyzeCardVisible() {
    this.byPartialText(ANALYZE_CARD_TEXT).should('be.visible');
    return this;
  }

  assertHistoryCardVisible() {
    this.byPartialText(HISTORY_CARD_TEXT).should('be.visible');
    return this;
  }

  assertLogoutCardVisible() {
    this.byPartialText(LOGOUT_CARD_TEXT).should('be.visible');
    return this;
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /** Navigates to the Capture screen. */
  clickAnalyzeImage() {
    this.clickByText(ANALYZE_CARD_TEXT);
    return new CapturePage();
  }

  /** Opens Profile through the router URL, avoiding flaky React Native Web card clicks. */
  clickProfile() {
    cy.visit('/profile');
    cy.location('pathname').should('include', '/profile');
    return new ProfilePage();
  }

  /** Clicks "Log Out" and waits for the Welcome screen to re-appear. */
  clickLogout() {
    this.clickByText(LOGOUT_CARD_TEXT);
    return new WelcomePage();
  }
}
