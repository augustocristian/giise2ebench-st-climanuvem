package epigijon.climanuvem.e2e.functional.tests.e2e;

import epigijon.climanuvem.e2e.functional.common.BaseLoggedClass;
import epigijon.climanuvem.e2e.functional.common.TestAccount;
import epigijon.climanuvem.e2e.functional.pages.RegisterPage;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Selenium system tests for account creation, derived from the Base Choice
 * table for username, email, password and confirmation alternatives.
 */
class TestRegisterSystem extends BaseLoggedClass {

    private static final String VALID_USERNAME_20 = "usuarioPrueba1234567";
    private static final String USERNAME_2 = "ab";
    private static final String USERNAME_21 = "usuarioPrueba12345678";
    private static final String VALID_PASSWORD = "Test12";
    private static final String PASSWORD_5 = "Test1";
    private static final String PASSWORD_NO_UPPERCASE = "test12";
    private static final String PASSWORD_NO_NUMBER = "Testaa";
    private static final String DIFFERENT_CONFIRM_PASSWORD = "Other1";

    @Test
    @DisplayName("BASE - Valid account data creates the account")
    void validAccountDataCreatesAccount() {
        String email = uniqueRegisterEmail();

        try {
            RegisterPage registerPage = openRegisterPage()
                    .register(VALID_USERNAME_20, email, VALID_PASSWORD, VALID_PASSWORD)
                    .waitForVerificationDialog();

            Assertions.assertTrue(
                    registerPage.isVerificationDialogVisible(),
                    "Valid registration data must create the account and show email-verification guidance");
        } finally {
            deleteFirebaseAccountIfConfigured(email, VALID_PASSWORD);
        }
    }

    @Test
    @DisplayName("2 - Username and email validation errors are rejected")
    void usernameAndEmailValidationErrorsAreRejected() {
        TestAccount existingAccount = loginAccount();

        Assertions.assertAll(
                () -> assertRegistrationRejected("", uniqueRegisterEmail(), VALID_PASSWORD, VALID_PASSWORD,
                        "Empty username must be rejected"),
                () -> assertRegistrationRejected(USERNAME_2, uniqueRegisterEmail(), VALID_PASSWORD, VALID_PASSWORD,
                        "Two-character username must be rejected"),
                () -> assertRegistrationRejected(USERNAME_21, uniqueRegisterEmail(), VALID_PASSWORD, VALID_PASSWORD,
                        "Twenty-one-character username must be rejected"),
                () -> assertRegistrationRejected(VALID_USERNAME_20, "correo-invalido", VALID_PASSWORD, VALID_PASSWORD,
                        "Invalid email must be rejected"),
                () -> assertRegistrationRejected(VALID_USERNAME_20, existingAccount.getEmail(), VALID_PASSWORD, VALID_PASSWORD,
                        "Email already in use must be rejected")
        );
    }

    @Test
    @DisplayName("3 - Password and confirmation validation errors are rejected")
    void passwordAndConfirmationValidationErrorsAreRejected() {
        Assertions.assertAll(
                () -> assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), "", "",
                        "Empty password must be rejected"),
                () -> assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), PASSWORD_5, PASSWORD_5,
                        "Five-character password must be rejected"),
                () -> assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(),
                        PASSWORD_NO_UPPERCASE, PASSWORD_NO_UPPERCASE,
                        "Password without uppercase letters must be rejected"),
                () -> assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(),
                        PASSWORD_NO_NUMBER, PASSWORD_NO_NUMBER,
                        "Password without numbers must be rejected"),
                () -> assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(),
                        VALID_PASSWORD, DIFFERENT_CONFIRM_PASSWORD,
                        "Non-matching password confirmation must be rejected")
        );
    }

    private RegisterPage openRegisterPage() {
        return onWelcomePage()
                .clickLoginButton()
                .clickRegisterLink();
    }

    private void assertRegistrationRejected(String username, String email, String password,
                                            String confirmPassword, String message) {
        RegisterPage registerPage = openRegisterPage()
                .register(username, email, password, confirmPassword);

        Assertions.assertTrue(
                registerPage.waitForRegisterFailure().hasRegisterErrorOrValidation(),
                message);
    }

    private String uniqueRegisterEmail() {
        return "climanuvem.test+" + System.currentTimeMillis() + "@" + registerEmailDomain;
    }
}
