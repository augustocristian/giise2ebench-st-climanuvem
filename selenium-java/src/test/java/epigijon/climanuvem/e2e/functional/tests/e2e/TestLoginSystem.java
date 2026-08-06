package epigijon.climanuvem.e2e.functional.tests.e2e;

import epigijon.climanuvem.e2e.functional.common.BaseLoggedClass;
import epigijon.climanuvem.e2e.functional.common.TestAccount;
import epigijon.climanuvem.e2e.functional.pages.HomePage;
import epigijon.climanuvem.e2e.functional.pages.LoginPage;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;

/**
 * Selenium system tests for the login functionality, derived from the Base
 * Choice table for guest, Google, email and password alternatives.
 */
class TestLoginSystem extends BaseLoggedClass {

    @Test
    @DisplayName("BASE - Guest login reaches Home")
    void guestLoginReachesHome() {
        HomePage guestHomePage = loginAsGuest();
        Assertions.assertTrue(
                guestHomePage.isWelcomeMessageVisible(),
                "Guest login must reach the Home screen");
    }

    @Test
    @DisplayName("BASE - Google login provider flow is available")
    void googleLoginProviderFlowIsAvailable() {
        LoginPage loginPage = onWelcomePage().clickLoginButton();

        Assertions.assertAll(
                () -> Assertions.assertTrue(
                        loginPage.isGoogleLoginPresent(),
                        "Google login option must be available"),
                () -> Assertions.assertTrue(
                        loginPage.clickGoogleLoginStartsProvider(),
                        "Clicking Google login must start the provider flow")
        );
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("loginAccounts")
    @DisplayName("2 - Existing email with correct password reaches Home")
    void existingEmailWithCorrectPasswordReachesHome(TestAccount account) {
        HomePage emailHomePage = onWelcomePage()
                .clickLoginButton()
                .login(account.getEmail(), account.getPassword())
                .waitForHome();
        Assertions.assertTrue(
                emailHomePage.isWelcomeMessageVisible(),
                "Existing email with correct password must reach the Home screen");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("loginAccounts")
    @DisplayName("3 - Invalid email/password login attempts are rejected")
    void invalidEmailPasswordLoginAttemptsAreRejected(TestAccount account) {
        TestAccount unknown = unknownAccount();
        LoginPage loginPage = onWelcomePage().clickLoginButton();

        Assertions.assertAll(
                () -> assertLoginRejected(loginPage, account.getEmail(), "",
                        "Existing email with empty password must remain on Login and show validation or an error"),
                () -> assertLoginRejected(loginPage, unknown.getEmail(), unknown.getPassword(),
                        "Unknown email with empty password must remain on Login and show validation or an error"),
                () -> assertLoginRejected(loginPage, "", "",
                        "Empty credentials must remain on Login and show validation"),
                () -> assertLoginRejected(loginPage, account.getEmail(), unknown.getPassword(),
                        "Existing email with incorrect password must remain on Login and show an error")
        );
    }

    private void assertLoginRejected(LoginPage loginPage, String email, String password, String message) {
        loginPage.login(email, password);

        try {
            Assertions.assertTrue(
                    loginPage.waitForLoginFailure().hasLoginErrorOrValidation(),
                    message);
        } finally {
            loginPage.closeLoginFeedbackIfPresent();
        }
    }
}
