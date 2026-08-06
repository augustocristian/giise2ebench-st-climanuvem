const { defineConfig } = require('cypress');
const { loadAccounts } = require('./cypress/tasks/testAccounts');
const analysisApi = require('./cypress/tasks/analysisApi');

module.exports = defineConfig({
  e2e: {
    // Reassigned below from env.FRONTEND_URL once Cypress has merged
    // cypress.env.json / CYPRESS_* process env / --env over these defaults.
    baseUrl: 'http://localhost:5173',
    specPattern: 'cypress/e2e/**/*.cy.js',
    supportFile: 'cypress/support/e2e.js',
    fixturesFolder: 'cypress/fixtures',
    defaultCommandTimeout: 30000,
    requestTimeout: 15000,
    responseTimeout: 30000,
    retries: { runMode: 1, openMode: 0 },
    env: {
      SUT_URL: 'http://localhost:8000',
      FRONTEND_URL: 'http://localhost:5173',
      TEST_TOKEN: 'test-token-climanuvem',
      ANALYSIS_TIMEOUT_MS: 360000,
      ACCOUNTS_FILE: 'cypress/fixtures/accounts.local.csv',
      REGISTER_EMAIL_DOMAIN: 'gmail.com',
      FIREBASE_WEB_API_KEY: '',
      REAL_OLLAMA_TESTS: false,
    },
    setupNodeEvents(on, config) {
      config.baseUrl = config.env.FRONTEND_URL;

      config.env.testAccounts = loadAccounts(config.env.ACCOUNTS_FILE);

      on('task', {
        uploadImage: analysisApi.uploadImage,
        uploadWithoutFile: analysisApi.uploadWithoutFile,
        deleteFirebaseAccount: analysisApi.deleteFirebaseAccount,
        log(message) {
          console.log(message);
          return null;
        },
      });

      return config;
    },
  },
});
