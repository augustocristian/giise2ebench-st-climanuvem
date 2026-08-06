# EPI-ClimaNuvem — Test Suite

Test suite for the [EPI-ClimaNuvem](https://gitlab.com/HP-SCDS/Observatorio/2025-2026/climanuvem/epi-climanuvem) application.

Covers two test layers:
- **API tests** — HTTP-level tests against the FastAPI backend (no browser needed)
- **Login system tests** — Selenium/JUnit tests that drive the Expo web frontend in Chrome

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Java (JDK) | 11 |
| Maven | 3.8 |
| Docker + Docker Compose | 24 |
| Git | any recent |
| Chrome | any recent (for Selenium tests) |

---

## Quick start

### 1 — Deploy the SUT

The deploy script clones the SUT from GitLab on first run, builds the Docker images, and waits until both the backend and frontend are ready.

```bash
# Linux / macOS
./deploy-local.sh

# Windows PowerShell
./deploy-local.ps1
```

Services started:

| Service | URL |
|---|---|
| Backend (FastAPI) | http://localhost:8000 |
| Frontend (Expo web) | http://localhost:5173 |

### 2 — Run the tests

```bash
# All tests
mvn test

# API tests only
mvn test -Dtest="TestApi*"

# Login system tests only (opens Chrome)
mvn test -Dtest="TestLoginSystem"

# Login system tests headless (for CI or no monitor)
mvn test -Dtest="TestLoginSystem" -DCI=true

# Account-creation system tests
mvn test -Dtest="TestRegisterSystem" -DCI=true

# Profile-configuration system tests
mvn test -Dtest="TestProfileSystem" -DCI=true

# Single class
mvn test -Dtest=TestApiCancel
```

### Real image-analysis tests with Ollama

The normal deployment starts the backend with `DISABLE_WORKER=true`, so `mvn test`
does not run the real image-analysis suite and does not require Ollama. To test
the full image-analysis flow, start the optional Ollama environment explicitly:

```bash
# Linux / macOS
./deploy-local.sh --with-ollama

# Windows PowerShell
./deploy-local.ps1 -WithOllama
```

Then run only the real image-analysis tests:

```bash
mvn test -Dtest=TestApiImageAnalysisSystem -DREAL_OLLAMA_TESTS=true
```

`--with-ollama` / `-WithOllama` enables the analysis worker, starts an Ollama
container, and pulls `${OLLAMA_MODEL:-gemma4:e4b}`. The first run can take longer
while the model is downloaded. These tests validate the real upload and
processing flow: image upload, history polling, cloud detection, explainability
boxes, no-cloud images, and file validation cases.

### 3 — Tear down

```bash
./deploy-local.sh --down    # Linux / macOS
./deploy-local.ps1 -Down    # Windows PowerShell
```

Teardown removes the test containers, network, PostgreSQL volume, and Ollama
volume so the next run starts from a fully clean local environment.

---

## Configuration

Selenium account data is loaded from a CSV file instead of individual email/password properties.

The account file path is resolved in this priority order:

1. Maven system property: `-DACCOUNTS_FILE=path/to/accounts.csv`.
2. Environment variable: `ACCOUNTS_FILE`.
3. `ACCOUNTS_FILE` in `src/test/resources/test.properties`.

Create your local account file from the template:

```bash
cp src/test/resources/accounts.template.csv src/test/resources/accounts.local.csv
```

`accounts.local.csv` is ignored by Git and should contain the real accounts used by local or CI runs:

```csv
role,email,password,verified,description
login_user,user@example.com,secret,true,Existing account for login tests
profile_user,verified-user@example.com,secret,true,Verified account for profile tests
unknown_user,missing@example.test,wrong-password,false,Non-existing account for negative login tests
```

Roles:

- `login_user`: existing account used by `TestLoginSystem` and by the "email already in use" registration case.
- `profile_user`: verified account used by authenticated profile tests. It may be the same account as `login_user`.
- `unknown_user`: account expected not to exist, used for negative login attempts.

`TestLoginSystem` and `TestProfileSystem` are parameterized: if the CSV contains several `login_user` or `profile_user` rows, the relevant tests run once per row.

| Property | Default | Description |
|---|---|---|
| `SUT_URL` | `http://localhost:8000` | Backend base URL |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend base URL (Selenium tests) |
| `TEST_TOKEN` | `test-token-climanuvem` | Auth token injected by API tests |
| `HTTP_TIMEOUT_MS` | `10000` | HTTP client timeout for API tests |
| `ANALYSIS_TIMEOUT_MS` | `360000` | Maximum wait for real image-analysis completion |
| `ACCOUNTS_FILE` | `src/test/resources/accounts.local.csv` | CSV file with Selenium test accounts |
| `REGISTER_EMAIL_DOMAIN` | `gmail.com` | Domain used for unique registration-test emails |
| `FIREBASE_WEB_API_KEY` | _(unset)_ | Optional Firebase Web API key used to delete the account created by `TestRegisterSystem` |
| `TJOB_NAME` | `local` | Separates build outputs in CI |
| `CI` | _(unset)_ | Set to `true` for headless Chrome |

`TestRegisterSystem` creates the successful-registration account with a unique email address using `REGISTER_EMAIL_DOMAIN` and expects the email-verification dialog shown by the app. If `FIREBASE_WEB_API_KEY` is configured, the test deletes that Firebase Auth account at the end; otherwise the unique address prevents future test collisions.

---

## Test architecture

```
src/test/java/epigijon/climanuvem/e2e/functional/
├── common/
│   ├── BaseApiClass.java       HTTP helpers, multipart upload, JSON fixtures
│   ├── BaseLoggedClass.java    Selenium browser lifecycle and login configuration
│   ├── TestAccount.java        Account row used by parameterized Selenium tests
│   └── TestAccounts.java       CSV loader and role lookup for Selenium accounts
├── pages/                      Page Object Model — one class per screen
│   ├── BasePage.java           Shared wait, click, fill, isPresent helpers
│   ├── WelcomePage.java
│   ├── LoginPage.java
│   ├── RegisterPage.java
│   ├── HomePage.java
│   └── CapturePage.java
└── tests/
    ├── api/                    HTTP-level tests (no browser)
    │   ├── TestApiPing.java
    │   ├── TestApiAuth.java
    │   ├── TestApiAnalysis.java
    │   ├── TestApiImageAnalysisSystem.java
    │   ├── TestApiHistory.java
    │   ├── TestApiDelete.java
    │   └── TestApiCancel.java
    └── e2e/                    Selenium system tests (Page Object pattern)
        ├── TestLoginSystem.java
        ├── TestRegisterSystem.java
        └── TestProfileSystem.java
```

Selenium account data lives under `src/test/resources/`:

```
src/test/resources/
├── test.properties             URLs, TEST_TOKEN, ACCOUNTS_FILE and non-sensitive defaults
├── accounts.template.csv       Versioned example for Selenium account data
├── accounts.local.csv          Local/CI account data, ignored by Git
└── log4j2.xml
```

Page object navigation is typed — every action returns the next screen:

```java
// No auth required
WelcomePage welcome = onWelcomePage();
LoginPage   login   = welcome.clickLoginButton();
RegisterPage reg    = login.clickRegisterLink();

// Authenticated flow
HomePage    home    = loginAsGuest();          // Firebase anonymous auth
CapturePage capture = home.clickAnalyzeImage();
WelcomePage back    = home.clickLogout();
```

---

## Test mode

The backend is started with `TEST_MODE=true` and `DISABLE_WORKER=true` (see `docker-compose.test.yml`):

- **Any Bearer token** is accepted — API tests use a fixed token; Selenium guest-login tests use real Firebase anonymous tokens.
- **Firebase is not initialised** — no service account key is needed.
- **Ollama worker is disabled** — analyses stay in `analyzing` state, making cancel tests deterministic.

The optional real image-analysis suite has its own Ollama deployment flow in
the quick-start section above.
