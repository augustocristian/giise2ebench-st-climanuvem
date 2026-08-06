const js = require('@eslint/js');
const globals = require('globals');
const cypressPlugin = require('eslint-plugin-cypress');

module.exports = [
  js.configs.recommended,
  {
    // cypress.config.js and the Node-side tasks it registers.
    files: ['cypress.config.js', 'cypress/tasks/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
      globals: { ...globals.node },
    },
  },
  {
    // Specs and support modules run in the browser, using ES module syntax.
    files: ['cypress/e2e/**/*.js', 'cypress/support/**/*.js'],
    plugins: { cypress: cypressPlugin },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.mocha,
        cy: 'readonly',
        Cypress: 'readonly',
        expect: 'readonly',
        assert: 'readonly',
      },
    },
    rules: {
      ...cypressPlugin.configs.recommended.rules,
    },
  },
];
