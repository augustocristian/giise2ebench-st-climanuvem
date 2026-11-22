package epigijon.climanuvem.e2e.functional.tests.e2e;

import epigijon.climanuvem.e2e.functional.common.BaseLoggedClass;
import epigijon.climanuvem.e2e.functional.common.TestAccount;
import epigijon.climanuvem.e2e.functional.pages.ProfilePage;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;

/**
 * Selenium system tests for profile configuration, derived from the
 * hierarchical
 * test design for guest and authenticated sessions.
 */
class TestProfileSystem extends BaseLoggedClass {

        private static final String USERNAME_0 = "";
        private static final String USERNAME_2 = "ab";
        private static final String USERNAME_20_A = "perfilPrueba12345678";
        private static final String USERNAME_20_B = "perfilPrueba87654321";
        private static final String USERNAME_21 = "perfilPrueba123456789";

        @Test
        @DisplayName("Guest session - theme and language preferences can be selected")
        void guestCanSelectThemeAndLanguagePreferences() {
                ProfilePage profilePage = openGuestProfile();

                profilePage.chooseLightTheme();
                Assertions.assertTrue(profilePage.hasStoredTheme("light"),
                                "Guest profile must store the light theme preference");

                profilePage.chooseDarkTheme();
                Assertions.assertTrue(profilePage.hasStoredTheme("dark"),
                                "Guest profile must store the dark theme preference");

                profilePage.chooseSystemTheme();
                Assertions.assertTrue(profilePage.hasStoredTheme("system"),
                                "Guest profile must store the system theme preference");

                profilePage.chooseEnglishLanguage();
                Assertions.assertTrue(profilePage.hasStoredLanguage("en"),
                                "Guest profile must store the English language preference");

                profilePage.chooseSpanishLanguage();
                Assertions.assertTrue(profilePage.hasStoredLanguage("es"),
                                "Guest profile must store the Spanish language preference");

                profilePage.chooseSystemLanguage();
                Assertions.assertTrue(profilePage.hasStoredLanguage("system"),
                                "Guest profile must store the system language preference");
        }

        @ParameterizedTest(name = "{0}")
        @MethodSource("profileAccounts")
        @DisplayName("Authenticated session - delete account opens confirmation and can be cancelled")
        void authenticatedDeleteAccountShowsConfirmationAndCanBeCancelled(TestAccount account) {
                ProfilePage profilePage = openAuthenticatedProfile(account)
                                .openDeleteAccountDialog();

                Assertions.assertTrue(profilePage.isDeleteConfirmVisible(),
                                "Delete account must open a confirmation dialog");

                profilePage.cancelDeleteAccount();
                Assertions.assertFalse(profilePage.isDeleteConfirmVisible(),
                                "Delete confirmation must close after cancelling");
        }

        @ParameterizedTest(name = "{0}")
        @MethodSource("profileAccounts")
        @DisplayName("Authenticated session - username length rules are enforced")
        void authenticatedUsernameLengthRulesAreEnforced(TestAccount account) {
                ProfilePage profilePage = openAuthenticatedProfile(account);
                String validUsername20 = username20DifferentFrom(profilePage.currentUsername());

                profilePage.updateUsername(validUsername20)
                                .waitForProfileFeedback()
                                .closeProfileFeedback();
                Assertions.assertTrue(profilePage.isUsernameSectionVisible(),
                                "Twenty-character username must be accepted and keep the user on Profile");

                profilePage.setUsername(USERNAME_0);
                Assertions.assertFalse(profilePage.isSaveButtonEnabled(),
                                "Zero-character username must keep the save action disabled");

                profilePage.setUsername(USERNAME_2);
                Assertions.assertFalse(profilePage.isSaveButtonEnabled(),
                                "Two-character username must keep the save action disabled");

                profilePage.setUsername(USERNAME_21);
                Assertions.assertFalse(profilePage.isSaveButtonEnabled(),
                                "Twenty-one-character username must keep the save action disabled");
        }

        @ParameterizedTest(name = "{0}")
        @MethodSource("profileAccounts")
        @DisplayName("Authenticated session - theme and language preferences can be selected")
        void authenticatedCanSelectThemeAndLanguagePreferences(TestAccount account) {
                ProfilePage profilePage = openAuthenticatedProfile(account);

                profilePage.chooseLightTheme();
                Assertions.assertTrue(profilePage.hasStoredTheme("light"),
                                "Authenticated profile must store the light theme preference");

                profilePage.chooseDarkTheme();
                Assertions.assertTrue(profilePage.hasStoredTheme("dark"),
                                "Authenticated profile must store the dark theme preference");

                profilePage.chooseSystemTheme();
                Assertions.assertTrue(profilePage.hasStoredTheme("system"),
                                "Authenticated profile must store the system theme preference");

                profilePage.chooseEnglishLanguage();
                Assertions.assertTrue(profilePage.hasStoredLanguage("en"),
                                "Authenticated profile must store the English language preference");

                profilePage.chooseSpanishLanguage();
                Assertions.assertTrue(profilePage.hasStoredLanguage("es"),
                                "Authenticated profile must store the Spanish language preference");

                profilePage.chooseSystemLanguage();
                Assertions.assertTrue(profilePage.hasStoredLanguage("system"),
                                "Authenticated profile must store the system language preference");
        }

        private ProfilePage openGuestProfile() {
                ProfilePage profilePage = loginAsGuest().clickProfile().waitForGuestProfile();
                Assertions.assertTrue(profilePage.isGuestPreferencesVisible(),
                                "Guest profile must show guest preferences");
                return profilePage;
        }

        private ProfilePage openAuthenticatedProfile(TestAccount account) {
                ProfilePage profilePage = onWelcomePage()
                                .clickLoginButton()
                                .login(account.getEmail(), account.getPassword())
                                .waitForHome()
                                .clickProfile()
                                .waitForAuthenticatedProfile();
                Assertions.assertAll(
                                () -> Assertions.assertTrue(profilePage.isUsernameSectionVisible(),
                                                "Authenticated profile must show username configuration"),
                                () -> Assertions.assertTrue(profilePage.isDeleteAccountVisible(),
                                                "Authenticated profile must show delete-account action"));
                return profilePage;
        }

        private String username20DifferentFrom(String currentUsername) {
                if (USERNAME_20_A.equals(currentUsername)) {
                        return USERNAME_20_B;
                }
                return USERNAME_20_A;
        }
}
