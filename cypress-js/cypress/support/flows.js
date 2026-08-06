// System-test entry points, mirroring selenium-java's BaseLoggedClass.
// Cypress resets the browser context (cookies/localStorage/page) between
// every `it()` automatically, so there is no ChromeDriver lifecycle to
// manage here — these are the navigation shortcuts every system spec starts
// from, kept as plain functions (not custom commands) because they return
// Page Object instances rather than a jQuery/DOM subject.
import WelcomePage from './pages/WelcomePage';
import { profileAccount } from './common/testAccounts';

/** Visits the frontend root and returns a WelcomePage once it has mounted. */
export function onWelcomePage() {
  cy.visit('/');
  return new WelcomePage();
}

/**
 * Clicks "Continuar como invitado" and returns the Home page once loaded.
 * Firebase anonymous auth is invoked; the backend accepts the resulting
 * token because TEST_MODE=true accepts any Bearer token.
 */
export function loginAsGuest() {
  return onWelcomePage().clickAnonymousLogin();
}

export function loginAsProfileUser() {
  const account = profileAccount();
  return onWelcomePage().clickLoginButton().login(account.email, account.password).waitForHome();
}

/**
 * Best-effort cleanup for accounts created by TestRegisterSystem-equivalent
 * specs. No-ops (with a console warning from the Node task) when
 * FIREBASE_WEB_API_KEY is not configured.
 */
export function deleteFirebaseAccountIfConfigured(email, password) {
  return cy.task('deleteFirebaseAccount', {
    apiKey: Cypress.env('FIREBASE_WEB_API_KEY'),
    email,
    password,
  });
}
