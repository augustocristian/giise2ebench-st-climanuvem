# EPI-ClimaNuvem — Puppeteer (pyppeteer) + Python Test Suite

Python test suite for [EPI-ClimaNuvem](https://gitlab.com/HP-SCDS/Observatorio/2025-2026/climanuvem/epi-climanuvem),
covering the same scenarios as the [`selenium-java`](../selenium-java) suite in this repository. Browser
automation uses [pyppeteer](https://github.com/pyppeteer/pyppeteer) (the Python port of Puppeteer); the project
itself follows the same Poetry/pytest layout as [`example/`](../example) (this repo's Python project template).

Covers two test layers:
- **API tests** (`tests/api/`) — HTTP-level tests against the FastAPI backend via [`requests`](https://requests.readthedocs.io/) (no browser needed)
- **System tests** (`tests/e2e/`) — pyppeteer-driven tests against the Expo web frontend, using a Page Object Model

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.12 |
| [Poetry](https://python-poetry.org/) | 2.0 |
| Docker + Docker Compose | 24 |
| Git | any recent |

Poetry can be installed with `pip install poetry` (or any method from the
[official docs](https://python-poetry.org/docs/#installation)) if it isn't already on your machine.

---

## Quick start

### 1 — Deploy the SUT in test mode

`sut/docker-compose.test.yml` (shared by every test suite in this repo — not duplicated per-suite) builds the
backend and frontend from `sut/backend` and `sut/frontend` and starts them with `TEST_MODE=true` — no Firebase
project or Ollama needed for the default suite.

```bash
docker compose -f ../sut/docker-compose.test.yml up --build -d
```

Services started:

| Service | URL |
|---|---|
| Backend (FastAPI) | http://localhost:8000 |
| Frontend (Expo web) | http://localhost:5173 |

### 2 — Install dependencies

```bash
poetry install
```

The first pyppeteer launch downloads a matching Chromium revision into a local cache (`~/.pyppeteer` by default,
or `.local-chromium/` if `PYPPETEER_HOME` is set to the project directory — see `.gitignore`); this only happens
once.

### 3 — Run the tests

```bash
poetry run pytest                          # everything (API + system)
poetry run pytest tests/api                 # API tests only
poetry run pytest tests/e2e                  # system tests only (drives Chromium)

poetry run pytest tests/e2e/test_login_system.py
poetry run pytest tests/e2e/test_register_system.py
poetry run pytest tests/e2e/test_profile_system.py

CI=true poetry run pytest tests/e2e          # headless Chromium (for CI or no display)
```

### Real image-analysis tests with Ollama

The default deployment starts the backend with `DISABLE_WORKER=true`, so `poetry run pytest` skips the real
image-analysis suite and does not require Ollama. To exercise the full image-analysis flow, layer the optional
Ollama compose file on top:

```bash
docker compose -f ../sut/docker-compose.test.yml -f ../sut/docker-compose.ollama-test.yml up --build -d
```

Then run only the real image-analysis suite:

```bash
REAL_OLLAMA_TESTS=true poetry run pytest tests/api/test_image_analysis_system.py
```

`REAL_OLLAMA_TESTS=true` enables the analysis worker, starts an Ollama container, and pulls
`${OLLAMA_MODEL:-gemma4:e4b}`. The first run can take longer while the model downloads. These tests validate the
real upload and processing flow: image upload, history polling, cloud detection, explainability boxes, no-cloud
images, and file validation cases.

### 4 — Tear down

```bash
docker compose -f ../sut/docker-compose.test.yml -f ../sut/docker-compose.ollama-test.yml down --volumes
```

(Omit `-f ../sut/docker-compose.ollama-test.yml` if you never started it; `--volumes` removes the Postgres and
Ollama data volumes for a clean next run.)

---

## Configuration

Account data for the system suite is loaded from a CSV file instead of individual email/password variables,
exactly like `selenium-java`.

Create your local account file from the template:

```bash
cp tests/resources/accounts.template.csv tests/resources/accounts.local.csv
```

`accounts.local.csv` is ignored by Git and should contain the real accounts used by local or CI runs:

```csv
role,email,password,verified,description
login_user,user@example.com,secret,true,Existing account for login tests
profile_user,verified-user@example.com,secret,true,Verified account for profile tests
unknown_user,missing@example.test,wrong-password,false,Non-existing account for negative login tests
```

Roles:

- `login_user`: existing account used by `test_login_system.py` and by the "email already in use" registration case.
- `profile_user`: verified account used by authenticated profile tests. May be the same account as `login_user`.
- `unknown_user`: account expected not to exist, used for negative login attempts.

`test_login_system.py` and `test_profile_system.py` iterate every row for `login_user`/`profile_user` inside a
single test method, using `self.subTest(...)` per account — Python's built-in equivalent of JUnit's
`@ParameterizedTest`/`@MethodSource` (a `subTest` failure is recorded but doesn't stop the rest of the test).

All values below are plain environment variables, read by `climanuvem/common/config.py`:

| Variable | Default | Description |
|---|---|---|
| `SUT_URL` | `http://localhost:8000` | Backend base URL used by API tests |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend base URL used by system tests |
| `TEST_TOKEN` | `test-token-climanuvem` | Auth token injected by API tests |
| `HTTP_TIMEOUT_MS` | `10000` | HTTP client timeout for API tests |
| `ANALYSIS_TIMEOUT_MS` | `360000` | Maximum wait for real image-analysis completion |
| `ACCOUNTS_FILE` | `tests/resources/accounts.local.csv` | CSV file with system-test accounts |
| `REGISTER_EMAIL_DOMAIN` | `gmail.com` | Domain used for unique registration-test emails |
| `FIREBASE_WEB_API_KEY` | _(unset)_ | Optional Firebase Web API key used to delete the account created by `test_register_system.py` |
| `REAL_OLLAMA_TESTS` | `false` | Set `true` to enable `tests/api/test_image_analysis_system.py` |
| `CI` | _(unset)_ | Set to `true` for headless Chromium |
| `PYPPETEER_EXECUTABLE_PATH` | _(unset)_ | Path to a Chrome/Chromium binary — see note below |

`test_register_system.py`'s account-creation test builds a unique email address from `REGISTER_EMAIL_DOMAIN` and
expects the email-verification guidance shown by the app. If `FIREBASE_WEB_API_KEY` is configured, the test
deletes that Firebase Auth account afterward; otherwise the unique address just prevents future test collisions.

**If `poetry run pytest tests/e2e` fails with `Chromium downloadable not found`**: pyppeteer pins a specific
Chromium snapshot revision and downloads it on first launch; that revision is occasionally pruned from Google's
snapshot bucket before a new pyppeteer release updates the pin (a known, currently-open upstream issue — not
something this suite can fix). Point `PYPPETEER_EXECUTABLE_PATH` at any locally installed Chrome/Chromium
instead, e.g. on Windows:

```bash
export PYPPETEER_EXECUTABLE_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

---

## Test architecture

```
climanuvem/                    Installable package — page objects and shared test infrastructure
├── common/
│   ├── config.py                Environment-driven settings (SUT_URL, FRONTEND_URL, TEST_TOKEN, ...)
│   ├── api_client.py             ApiTestCase: HTTP helpers, multipart upload, JPEG fixture synthesis (Pillow)
│   ├── browser_session.py        BrowserSession (pyppeteer lifecycle) + BrowserTestCase (navigation entry points)
│   ├── test_account.py           Account row used by parameterized system tests
│   └── test_accounts.py          CSV loader and role lookup for system-test accounts
└── pages/                       Page Object Model — one class per screen
    ├── base_page.py               Shared locator factories + wait/click/fill primitives
    ├── welcome_page.py
    ├── login_page.py
    ├── register_page.py
    ├── home_page.py
    ├── capture_page.py
    └── profile_page.py

tests/
├── conftest.py                  pytest hooks: log the start/end of every test's setup/teardown
├── context.py                   sys.path bootstrap (matches example/tests/context.py)
├── resources/
│   ├── accounts.template.csv    Versioned example for system-test account data
│   └── accounts.local.csv       Local/CI account data, ignored by Git
├── api/                          HTTP-level tests (no browser)
│   ├── test_ping.py
│   ├── test_auth.py
│   ├── test_analysis.py
│   ├── test_cancel.py
│   ├── test_delete.py
│   ├── test_history.py
│   └── test_image_analysis_system.py
└── e2e/                           pyppeteer system tests (Page Object pattern)
    ├── test_login_system.py
    ├── test_register_system.py
    └── test_profile_system.py
```

Every test class is a `unittest.TestCase` subclass using plain `assert` statements (pytest rewrites `assert` for
readable failure output even inside `unittest.TestCase`), with `logger.debug(...)` marking the start/end of each
test — the same style as [`example/tests/test_basic.py`](../example/tests/test_basic.py). API tests subclass
`ApiTestCase`; system tests subclass `BrowserTestCase`.

Page objects navigate the same way `selenium-java`'s do — every action returns the next screen:

```python
# No auth required
welcome = self.on_welcome_page()
login = welcome.click_login_button()
register = login.click_register_link()

# Authenticated flow
home = self.login_as_guest()          # Firebase anonymous auth
capture = home.click_analyze_image()
back = home.click_logout()
```

### Why this isn't a line-for-line port

pyppeteer is asyncio-only, but every page object method here is exposed **synchronously** — matching both the
Selenium reference and this suite's `unittest.TestCase` style. `BrowserSession` owns one event loop per test;
every page object routes its awaits through `BasePage._run()`, which drives that loop with
`run_until_complete`. `ElementHandle.click()`/`.type()` dispatch real-enough browser events that React Native
Web's handlers pick up natively, so the JS-dispatched-click and native-setter plumbing selenium-java's
`BasePage` needed for WebDriver is not reproduced here.

Where a single JUnit `@Test` used `Assertions.assertAll(...)` to bundle several *independent* checks (login/
register validation, theme/language selection), each becomes a `self.subTest(...)` block here — `unittest`'s
built-in mechanism for exactly this: every sub-check still runs and is reported individually, instead of
stopping at the first failure the way a bare `assert` would.

The parameterized profile scenarios (`test_authenticated_*` in `test_profile_system.py`) open a *dedicated*
`BrowserSession` per account via `_authenticated_profile(...)` rather than reusing the test's shared session —
each account needs a logged-out Welcome screen to start from, and Firebase's persisted session would otherwise
carry over between accounts within the same test method. selenium-java sidesteps this because JUnit's
`@ParameterizedTest` re-runs `@BeforeEach` (a fresh ChromeDriver) for every row.

---

## Test mode

The backend is started with `TEST_MODE=true` and `DISABLE_WORKER=true` (see `../sut/docker-compose.test.yml`):

- **Any Bearer token** is accepted — API tests use a fixed token; system-test guest login uses real Firebase anonymous tokens.
- **Firebase is not initialised** — no service account key is needed.
- **Ollama worker is disabled** — analyses stay in `analyzing` state, making cancel tests deterministic.

The optional real image-analysis suite has its own Ollama deployment flow in the quick-start section above.
