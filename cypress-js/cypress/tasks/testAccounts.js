// Node-side CSV account loader, used once from cypress.config.js at startup.
// Mirrors selenium-java's TestAccounts: reads role,email,password,verified,description
// rows and groups them by role so specs can iterate the same way JUnit's
// @ParameterizedTest/@MethodSource did over TestAccounts.byRole(...).
const fs = require('fs');

const ROLE_LOGIN_USER = 'login_user';
const ROLE_PROFILE_USER = 'profile_user';
const ROLE_UNKNOWN_USER = 'unknown_user';

function splitCsvLine(line) {
  const values = [];
  let current = '';
  let quoted = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        quoted = !quoted;
      }
    } else if (ch === ',' && !quoted) {
      values.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  values.push(current);
  return values;
}

function parseLine(line, accountsFile) {
  const columns = splitCsvLine(line);
  if (columns.length < 5) {
    throw new Error(
      `Invalid accounts row in ${accountsFile}. Expected columns: role,email,password,verified,description. Row: ${line}`
    );
  }
  return {
    role: columns[0].trim(),
    email: columns[1].trim(),
    password: columns[2],
    verified: columns[3].trim().toLowerCase() === 'true',
    description: columns[4].trim(),
  };
}

/**
 * Loads and groups the accounts CSV. Returns an object keyed by role, each
 * value an array of accounts (possibly empty). Missing/unreadable files
 * resolve to empty groups rather than throwing, so specs that don't need
 * accounts still run; specs that do need one fail with a clear message.
 */
function loadAccounts(accountsFile) {
  const groups = { [ROLE_LOGIN_USER]: [], [ROLE_PROFILE_USER]: [], [ROLE_UNKNOWN_USER]: [] };

  if (!fs.existsSync(accountsFile)) {
    console.warn(
      `[testAccounts] Accounts file not found: ${accountsFile}. ` +
        'Create it from cypress/fixtures/accounts.template.csv or set ACCOUNTS_FILE. ' +
        'Specs that require accounts will fail only when they request one.'
    );
    return groups;
  }

  const lines = fs.readFileSync(accountsFile, 'utf8').split(/\r?\n/);
  let headerSkipped = false;

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();
    if (trimmed === '' || trimmed.startsWith('#')) {
      continue;
    }
    if (!headerSkipped) {
      headerSkipped = true;
      if (trimmed.toLowerCase().startsWith('role,')) {
        continue;
      }
    }
    const account = parseLine(trimmed, accountsFile);
    if (!groups[account.role]) {
      groups[account.role] = [];
    }
    groups[account.role].push(account);
  }

  return groups;
}

module.exports = { loadAccounts, ROLE_LOGIN_USER, ROLE_PROFILE_USER, ROLE_UNKNOWN_USER };
