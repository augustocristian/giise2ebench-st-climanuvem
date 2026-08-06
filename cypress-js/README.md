# EPI-ClimaNuvem — Cypress Test Suite

Cypress + JavaScript test suite for [EPI-ClimaNuvem](https://gitlab.com/HP-SCDS/Observatorio/2025-2026/climanuvem/epi-climanuvem),
covering the same scenarios as the [`selenium-java`](../selenium-java) suite in this
repository, translated to Cypress idioms rather than ported line-for-line.

Covers two test layers:
- **API tests** (`cypress/e2e/api/`) — HTTP-level tests against the FastAPI backend via `cy.request`/`cy.task` (no browser UI involved)
- **System tests** (`cypress/e2e/system/`) — Cypress tests that drive the Expo web frontend, using a Page Object Model

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Node.js | 18 |
| npm | bundled with Node |
| Docker + Docker Compose | 24 |
| Git | any recent |

---

## Quick start

### 1 — Deploy the SUT in test mode

`sut/docker-compose.test.yml` (shared by every test suite in this repo — not
duplicated per-suite) builds the backend and frontend from `sut/backend` and
`sut/frontend` and starts them with `TEST_MODE=true` — no Firebase project or
Ollama needed for the default suite.

```bash
docker compose -f ../sut/docker-compose.test.yml up --build -d
```

Services started:

| Service | URL |
|---|---|
| Backend (FastAPI) | http://localhost:8000 |
| Frontend (Expo web) | http://localhost:5173 |

### 2 — Run the tests

```bash
npm install

npm test              # everything (API + system)
npm run test:api      # API tests only
npm run test:system   # system tests only (opens/drives Chrome headlessly)

npm run test:login    # a single system spec
npm run test:register
npm run test:profile

npm run cy:open       # interactive Cypress runner, for authoring/debugging
```

### Real image-analysis tests with Ollama

The default deployment starts the backend with `DISABLE_WORKER=true`, so
`npm test` skips the real image-analysis suite and does not require Ollama.
To exercise the full image-analysis flow, layer the optional Ollama compose
file on top:

```bash
docker compose -f ../sut/docker-compose.test.yml -f ../sut/docker-compose.ollama-test.yml up --build -d
```

Then run only the real image-analysis suite:

```bash
npm run test:image-analysis
```

This passes `--env REAL_OLLAMA_TESTS=true`; without it, `imageAnalysisSystem.cy.js`
is registered as skipped (`describe.skip`) rather than run. The first run can
take longer while `${OLLAMA_MODEL:-gemma4:e4b}` downloads. These tests
validate the real upload and processing flow: image upload, history polling,
cloud detection, explainability boxes, no-cloud images, and file-validation
edge cases.

### 3 — Tear down

```bash
docker compose -f ../sut/docker-compose.test.yml -f ../sut/docker-compose.ollama-test.yml down --volumes
```

(Omit `-f docker-compose.ollama-test.yml` if you never started it; `--volumes`
removes the Postgres and Ollama data volumes for a clean next run.)

---

## Configuration

Account data for the system suite is loaded from a CSV file instead of
individual email/password variables, exactly like `selenium-java`.

Create your local account file from the template:

```bash
cp cypress/fixtures/accounts.template.csv cypress/fixtures/accounts.local.csv
```

`accounts.local.csv` is ignored by Git and should contain the real accounts
used by local or CI runs:

```csv
role,email,password,verified,description
login_user,user@example.com,secret,true,Existing account for login tests
profile_user,verified-user@example.com,secret,true,Verified account for profile tests
unknown_user,missing@example.test,wrong-password,false,Non-existing account for negative login tests
```

Roles:

- `login_user`: existing account used by `login.cy.js` and by the "email already in use" registration case.
- `profile_user`: verified account used by authenticated profile tests. May be the same account as `login_user`.
- `unknown_user`: account expected not to exist, used for negative login attempts.

`login.cy.js`, `register.cy.js`, and `profile.cy.js` iterate every row for
`login_user`/`profile_user`, generating one Mocha `describe`/`it` block per
account — the Cypress equivalent of JUnit's
`@ParameterizedTest`/`@MethodSource`.

All values below are set in `cypress.config.js`'s `env` block and can be
overridden, in increasing order of precedence, via a `CYPRESS_<KEY>`
process/CI environment variable, a `cypress.env.json` file (gitignored), or
`--env KEY=value` on the CLI:

| Key | Default | Description |
|---|---|---|
| `SUT_URL` | `http://localhost:8000` | Backend base URL used by API specs |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend base URL — becomes Cypress's `baseUrl` |
| `TEST_TOKEN` | `test-token-climanuvem` | Auth token injected by API specs |
| `ANALYSIS_TIMEOUT_MS` | `360000` | Maximum wait for real image-analysis completion |
| `ACCOUNTS_FILE` | `cypress/fixtures/accounts.local.csv` | CSV file with system-test accounts |
| `REGISTER_EMAIL_DOMAIN` | `gmail.com` | Domain used for unique registration-test emails |
| `FIREBASE_WEB_API_KEY` | _(unset)_ | Optional Firebase Web API key used to delete the account created by `register.cy.js` |
| `REAL_OLLAMA_TESTS` | `false` | Set `true` to enable `imageAnalysisSystem.cy.js` |

`register.cy.js`'s account-creation test uses a unique email address built
from `REGISTER_EMAIL_DOMAIN` and expects the email-verification guidance
shown by the app. If `FIREBASE_WEB_API_KEY` is configured, the test deletes
that Firebase Auth account afterward; otherwise the unique address just
prevents future test collisions.

---

## Test architecture

```
cypress/
├── e2e/
│   ├── api/                    HTTP-level tests (no browser UI)
│   │   ├── ping.cy.js
│   │   ├── auth.cy.js
│   │   ├── analysis.cy.js
│   │   ├── history.cy.js
│   │   ├── delete.cy.js
│   │   ├── cancel.cy.js
│   │   └── imageAnalysisSystem.cy.js
│   └── system/                 Browser system tests (Page Object pattern)
│       ├── login.cy.js
│       ├── register.cy.js
│       └── profile.cy.js
├── support/
│   ├── e2e.js                  Loaded before every spec
│   ├── flows.js                Navigation entry points (onWelcomePage, loginAsGuest, ...)
│   ├── apiClient.js            URL builders, cy.request wrappers, upload/poll helpers
│   ├── common/
│   │   ├── testAccounts.js     Cypress.env('testAccounts') accessors, grouped by role
│   │   └── domChecks.js        Shared DOM predicates (feedback text, invalid inputs)
│   └── pages/                  Page Object Model — one class per screen
│       ├── BasePage.js
│       ├── WelcomePage.js
│       ├── LoginPage.js
│       ├── RegisterPage.js
│       ├── HomePage.js
│       ├── CapturePage.js
│       └── ProfilePage.js
├── tasks/                       Node-side Cypress tasks (registered in cypress.config.js)
│   ├── testAccounts.js          CSV loader, run once at config load
│   ├── testImages.js            Synthesizes JPEG fixtures with jpeg-js
│   └── analysisApi.js           Multipart upload + Firebase account cleanup (axios)
└── fixtures/
    ├── accounts.template.csv    Versioned example for system-test account data
    └── accounts.local.csv       Local/CI account data, ignored by Git
```

Page objects navigate the same way `selenium-java`'s do — every action
returns the next screen:

```js
// No auth required
const welcome = onWelcomePage();
const login = welcome.clickLoginButton();
const register = login.clickRegisterLink();

// Authenticated flow
const home = loginAsGuest();          // Firebase anonymous auth
const capture = home.clickAnalyzeImage();
const back = home.clickLogout();
```

### Why this isn't a line-for-line port

Cypress's `cy.get()`/`cy.contains()` are retry-and-wait-until-actionable by
default, so the `WebDriverWait` + JS-dispatched-click plumbing
`selenium-java`'s `BasePage` needed is not reproduced here — `{ force: true }`
covers the rare React Native Web element outside its real click box. Query
methods that returned a plain `boolean` in Java (`isXVisible()`) instead
return a Cypress chainable that yields a boolean here (e.g.
`loginPage.hasLoginErrorOrValidation().should('eq', true)`), since Cypress
commands are asynchronous and never resolve synchronously into JS control
flow. Where a single JUnit `@Test` used `Assertions.assertAll(...)` to bundle
several *independent* negative-path checks (login/register validation), each
sub-check becomes its own `it()` here — Mocha/Chai stop at the first failed
assertion within a test, so one scenario per `it()` keeps failure reporting
precise instead of hiding later checks behind an earlier failure.

Multipart image upload (and JPEG synthesis, which needs `jpeg-js`) run
through Node-side Cypress tasks (`cypress/tasks/`) instead of `cy.request`,
since `cy.request` only builds `application/x-www-form-urlencoded` bodies —
this is the direct equivalent of `BaseApiClass`'s Apache HttpClient
`MultipartEntityBuilder` usage, just on the Node side of the Cypress task
boundary.

---

## Test mode

The backend is started with `TEST_MODE=true` and `DISABLE_WORKER=true` (see
`../sut/docker-compose.test.yml`):

- **Any Bearer token** is accepted — API specs use a fixed token; system-test guest login uses real Firebase anonymous tokens.
- **Firebase is not initialised** — no service account key is needed.
- **Ollama worker is disabled** — analyses stay in `analyzing` state, making cancel tests deterministic.

The optional real image-analysis suite has its own Ollama deployment flow in
the quick-start section above.
