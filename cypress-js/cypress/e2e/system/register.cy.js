// Cypress system spec for account creation, derived from the same Base
// Choice table as selenium-java's TestRegisterSystem.
import { onWelcomePage, deleteFirebaseAccountIfConfigured } from '../../support/flows';
import { loginAccount } from '../../support/common/testAccounts';

const VALID_USERNAME_20 = 'usuarioPrueba1234567';
const USERNAME_2 = 'ab';
const USERNAME_21 = 'usuarioPrueba12345678';
const VALID_PASSWORD = 'Test12';
const PASSWORD_5 = 'Test1';
const PASSWORD_NO_UPPERCASE = 'test12';
const PASSWORD_NO_NUMBER = 'Testaa';
const DIFFERENT_CONFIRM_PASSWORD = 'Other1';

function openRegisterPage() {
  return onWelcomePage().clickLoginButton().clickRegisterLink();
}

function uniqueRegisterEmail() {
  return `climanuvem.test+${Date.now()}@${Cypress.env('REGISTER_EMAIL_DOMAIN')}`;
}

function assertRegistrationRejected(username, email, password, confirmPassword) {
  const registerPage = openRegisterPage().register(username, email, password, confirmPassword);
  registerPage.waitForRegisterFailure().hasRegisterErrorOrValidation().should('eq', true);
}

describe('Register system', () => {
  it('BASE - Valid account data creates the account', () => {
    const email = uniqueRegisterEmail();

    const registerPage = openRegisterPage()
      .register(VALID_USERNAME_20, email, VALID_PASSWORD, VALID_PASSWORD)
      .waitForVerificationDialog();

    registerPage.isVerificationDialogVisible().should('eq', true);
    deleteFirebaseAccountIfConfigured(email, VALID_PASSWORD);
  });

  describe('2 - Username and email validation errors are rejected', () => {
    it('Empty username is rejected', () => {
      assertRegistrationRejected('', uniqueRegisterEmail(), VALID_PASSWORD, VALID_PASSWORD);
    });

    it('Two-character username is rejected', () => {
      assertRegistrationRejected(USERNAME_2, uniqueRegisterEmail(), VALID_PASSWORD, VALID_PASSWORD);
    });

    it('Twenty-one-character username is rejected', () => {
      assertRegistrationRejected(USERNAME_21, uniqueRegisterEmail(), VALID_PASSWORD, VALID_PASSWORD);
    });

    it('Invalid email is rejected', () => {
      assertRegistrationRejected(VALID_USERNAME_20, 'correo-invalido', VALID_PASSWORD, VALID_PASSWORD);
    });

    it('Email already in use is rejected', () => {
      const existingAccount = loginAccount();
      assertRegistrationRejected(VALID_USERNAME_20, existingAccount.email, VALID_PASSWORD, VALID_PASSWORD);
    });
  });

  describe('3 - Password and confirmation validation errors are rejected', () => {
    it('Empty password is rejected', () => {
      assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), '', '');
    });

    it('Five-character password is rejected', () => {
      assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), PASSWORD_5, PASSWORD_5);
    });

    it('Password without uppercase letters is rejected', () => {
      assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), PASSWORD_NO_UPPERCASE, PASSWORD_NO_UPPERCASE);
    });

    it('Password without numbers is rejected', () => {
      assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), PASSWORD_NO_NUMBER, PASSWORD_NO_NUMBER);
    });

    it('Non-matching password confirmation is rejected', () => {
      assertRegistrationRejected(VALID_USERNAME_20, uniqueRegisterEmail(), VALID_PASSWORD, DIFFERENT_CONFIRM_PASSWORD);
    });
  });
});
