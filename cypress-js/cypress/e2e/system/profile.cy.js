// Cypress system spec for profile configuration, derived from the same
// hierarchical test design as selenium-java's TestProfileSystem.
import { onWelcomePage, loginAsGuest } from '../../support/flows';
import { profileAccounts } from '../../support/common/testAccounts';

const USERNAME_0 = '';
const USERNAME_2 = 'ab';
const USERNAME_20_A = 'perfilPrueba12345678';
const USERNAME_20_B = 'perfilPrueba87654321';
const USERNAME_21 = 'perfilPrueba123456789';

function openGuestProfile() {
  const profilePage = loginAsGuest().clickProfile().waitForGuestProfile();
  profilePage.assertGuestPreferencesVisible();
  return profilePage;
}

function openAuthenticatedProfile(account) {
  const profilePage = onWelcomePage()
    .clickLoginButton()
    .login(account.email, account.password)
    .waitForHome()
    .clickProfile()
    .waitForAuthenticatedProfile();
  profilePage.assertUsernameSectionVisible();
  profilePage.assertDeleteAccountVisible();
  return profilePage;
}

function assertThemeAndLanguagePreferencesSelectable(profilePage) {
  profilePage.chooseLightTheme();
  profilePage.hasStoredTheme('light').should('eq', true);

  profilePage.chooseDarkTheme();
  profilePage.hasStoredTheme('dark').should('eq', true);

  profilePage.chooseSystemTheme();
  profilePage.hasStoredTheme('system').should('eq', true);

  profilePage.chooseEnglishLanguage();
  profilePage.hasStoredLanguage('en').should('eq', true);

  profilePage.chooseSpanishLanguage();
  profilePage.hasStoredLanguage('es').should('eq', true);

  profilePage.chooseSystemLanguage();
  profilePage.hasStoredLanguage('system').should('eq', true);
}

function username20DifferentFrom(currentUsername) {
  return currentUsername === USERNAME_20_A ? USERNAME_20_B : USERNAME_20_A;
}

describe('Profile system', () => {
  it('Guest session - theme and language preferences can be selected', () => {
    assertThemeAndLanguagePreferencesSelectable(openGuestProfile());
  });

  profileAccounts().forEach((account) => {
    describe(`account: ${account.email}`, () => {
      it('Authenticated session - delete account opens confirmation and can be cancelled', () => {
        const profilePage = openAuthenticatedProfile(account).openDeleteAccountDialog();
        profilePage.assertDeleteConfirmVisible();
        profilePage.cancelDeleteAccount();
        profilePage.assertDeleteConfirmGone();
      });

      it('Authenticated session - username length rules are enforced', () => {
        const profilePage = openAuthenticatedProfile(account);

        profilePage.currentUsername().then((currentUsername) => {
          const validUsername20 = username20DifferentFrom(currentUsername);
          profilePage.updateUsername(validUsername20).waitForProfileFeedback().closeProfileFeedback();
          profilePage.assertUsernameSectionVisible();
        });

        profilePage.setUsername(USERNAME_0);
        profilePage.isSaveButtonEnabled().should('eq', false);

        profilePage.setUsername(USERNAME_2);
        profilePage.isSaveButtonEnabled().should('eq', false);

        profilePage.setUsername(USERNAME_21);
        profilePage.isSaveButtonEnabled().should('eq', false);
      });

      it('Authenticated session - theme and language preferences can be selected', () => {
        assertThemeAndLanguagePreferencesSelectable(openAuthenticatedProfile(account));
      });
    });
  });
});
