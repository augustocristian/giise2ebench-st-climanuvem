// Browser-side accessors over the account groups cypress.config.js loaded
// from ACCOUNTS_FILE at startup (see cypress/tasks/testAccounts.js) and
// exposed via Cypress.env('testAccounts'). Mirrors selenium-java's
// TestAccounts.byRole()/requiredSingle().
const ROLE_LOGIN_USER = 'login_user';
const ROLE_PROFILE_USER = 'profile_user';
const ROLE_UNKNOWN_USER = 'unknown_user';

function accountsByRole(role) {
  const accounts = Cypress.env('testAccounts') || {};
  return accounts[role] || [];
}

function requiredAccounts(role) {
  const accounts = accountsByRole(role);
  if (accounts.length === 0) {
    throw new Error(`Configure at least one ${role} in ${Cypress.env('ACCOUNTS_FILE')}.`);
  }
  return accounts;
}

export function loginAccounts() {
  return requiredAccounts(ROLE_LOGIN_USER);
}

export function profileAccounts() {
  return requiredAccounts(ROLE_PROFILE_USER);
}

export function loginAccount() {
  return requiredAccounts(ROLE_LOGIN_USER)[0];
}

export function profileAccount() {
  return requiredAccounts(ROLE_PROFILE_USER)[0];
}

export function unknownAccount() {
  return requiredAccounts(ROLE_UNKNOWN_USER)[0];
}
