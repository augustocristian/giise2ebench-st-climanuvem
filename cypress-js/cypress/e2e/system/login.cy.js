// Cypress system spec for the login functionality, derived from the same
// Base Choice table as selenium-java's TestLoginSystem. Each Java
// Assertions.assertAll(...) sub-check becomes its own it() here: Mocha/Chai
// stop at the first failed assertion within a test (no assertAll
// equivalent), so one scenario per it() keeps failure reporting precise.
import { onWelcomePage, loginAsGuest } from '../../support/flows';
import { loginAccounts, unknownAccount } from '../../support/common/testAccounts';

function assertLoginRejected(loginPage, email, password) {
  loginPage.login(email, password);
  loginPage.waitForLoginFailure().hasLoginErrorOrValidation().should('eq', true);
  loginPage.closeLoginFeedbackIfPresent();
}

describe('Login system', () => {
  it('BASE - Guest login reaches Home', () => {
    const home = loginAsGuest();
    home.assertWelcomeMessageVisible();
  });

  it('BASE - Google login provider flow is available', () => {
    const login = onWelcomePage().clickLoginButton();
    login.assertGoogleLoginVisible();
    login.clickGoogleLoginStartsProvider().should('eq', true);
  });

  loginAccounts().forEach((account) => {
    describe(`account: ${account.email}`, () => {
      it('2 - Existing email with correct password reaches Home', () => {
        const home = onWelcomePage().clickLoginButton().login(account.email, account.password).waitForHome();
        home.assertWelcomeMessageVisible();
      });

      it('3a - Existing email with empty password is rejected', () => {
        assertLoginRejected(onWelcomePage().clickLoginButton(), account.email, '');
      });

      it('3b - Unknown email with a password is rejected', () => {
        const unknown = unknownAccount();
        assertLoginRejected(onWelcomePage().clickLoginButton(), unknown.email, unknown.password);
      });

      it('3c - Empty credentials are rejected', () => {
        assertLoginRejected(onWelcomePage().clickLoginButton(), '', '');
      });

      it('3d - Existing email with incorrect password is rejected', () => {
        const unknown = unknownAccount();
        assertLoginRejected(onWelcomePage().clickLoginButton(), account.email, unknown.password);
      });
    });
  });
});
