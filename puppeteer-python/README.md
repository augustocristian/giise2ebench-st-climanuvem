# EPI-ClimaNuvem — Puppeteer + Python Test Suite

Puppeteer + Python (pytest) test suite for [EPI-ClimaNuvem](https://gitlab.com/HP-SCDS/Observatorio/2025-2026/climanuvem/epi-climanuvem),
covering the same scenarios as the [`selenium-java`](../selenium-java), [`cypress-js`](../cypress-js) and
[`playwright-csharp`](../playwright-csharp) suites in this repository, written in idiomatic Python rather than ported
line-for-line.

Puppeteer only exists for Node.js, and the Python port `pyppeteer` is abandoned and ships an obsolete Chromium. So the
tests stay in Python and talk to a small Node process (the *bridge*) that runs the current Puppeteer (pinned to
25.18.1).

Two test layers:

- **API tests** (`tests/api/`) — REST contract tests against the FastAPI backend through `requests` (no browser).
- **System tests** (`tests/e2e/`) — Puppeteer-driven tests against the Expo web frontend (English UI), using a Page
  Object Model and `data-testid` locators (ids listed in `climanuvem/common/test_ids.py`).

A third, tiny layer, `tests/bridge/`, smoke-tests the Python-Node bridge itself against a local page (no SUT needed).

---

## Architecture

```
 pytest (Python 3.12, asyncio)
   |  tests/e2e/*  ->  climanuvem/pages/* (page objects)  ->  climanuvem/browser (Browser, Page, Locator, TestId)
   |
   |  newline-delimited JSON-RPC over stdin/stdout  (asyncio subprocess, request ids)
   v
 Node bridge  (bridge/server.mjs, Node >= 22.12, puppeteer 25.18.1)
   |  Puppeteer Locators API (auto-waiting), browser contexts, evaluateOnNewDocument
   v
 Google Chrome (system install, channel "chrome", headless by default)  ->  ClimaNuvem frontend
```

- Auto-waiting comes from Puppeteer Locators on the Node side, so there are no polling waiters in Python for
  elements.
- Selectors are always CSS of the form `[data-testid='...']`, built with `TestId.of(...)`. There is no XPath and no
  CSS-class selector.
- The browser starts once per test session; each test gets its own isolated browser context (own cookies and storage).
- `nth` and `within` scoping is implemented with a Puppeteer custom query handler (`scope/...`), so scoped locators
  auto-wait too.
- The bridge exits (and closes Chrome) when Python closes its stdin, so a crashed test run does not leave Chrome behind.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| Python 3.12+ | pytest suite |
| Node.js 22.12+ (Node 22 in CI) | runs the bridge |
| Google Chrome | driven by Puppeteer (no browser is downloaded) |
| Docker + Docker Compose | runs the SUT |
| Git, Bash | the SUT scripts are Bash |

---

## Quick start

### 1 — Deploy the SUT

The stack is three layered Compose files: the production `sut/backend/docker-compose.yml`, the dev override (adds the
Firebase Auth emulator) and `docker-compose.test.override.yml` (test mode, ports, images). The shared helper
`selenium-java/scripts/sut-compose.sh` stacks them; run it from the repository root:

```bash
bash selenium-java/scripts/sut-compose.sh up --build -d db firebase-emulator backend frontend
ACCOUNTS_FILE="$PWD/puppeteer-python/tests/resources/accounts.local.csv" bash selenium-java/scripts/seed-firebase-emulator.sh
```

`seed-firebase-emulator.sh` creates the login/profile accounts in the Firebase emulator and writes the accounts CSV
used by the system tests (see [Configuration](#configuration)). To reuse prebuilt images (as CI does), set
`BACKEND_IMAGE` / `FRONTEND_IMAGE` / `FIREBASE_EMULATOR_IMAGE` and add `--no-build`. If port 8000 is taken, set
`BACKEND_PORT` and run the tests with `SUT_URL=http://localhost:<port>`.

| Service | URL |
|---|---|
| Backend (FastAPI) | http://localhost:8000 |
| Frontend (Expo web) | http://localhost:5173 |
| Firebase Auth emulator | http://localhost:9099 |

### 2 — Install the bridge and the Python dependencies

```bash
cd puppeteer-python

# Bridge: Puppeteer without downloading a browser (the system Chrome is used)
(cd bridge && PUPPETEER_SKIP_DOWNLOAD=true npm ci)

# Python
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install .                        # all dependencies are pinned in pyproject.toml (or: poetry install)
```

To use a different Chrome/Chromium binary, set `PUPPETEER_EXECUTABLE_PATH`. Set `NODE_BINARY` if `node` is not on the
`PATH`.

### 3 — Run the tests

```bash
python -m pytest                          # everything (bridge + API + system), headless
python -m pytest -m api                   # API tests only (no browser)
python -m pytest -m e2e                   # system tests only (drives Chrome)
python -m pytest -m bridge                # bridge smoke test (no SUT needed)
HEADED=1 python -m pytest -m e2e          # show the browser

python -m pytest tests/e2e/test_login_system.py
python -m pytest tests/e2e/test_register_system.py
python -m pytest tests/e2e/test_profile_system.py

python -m pytest tests --junitxml=results/junit.xml
```

The `api`, `e2e` and `bridge` markers are added automatically from the test folder (`tests/conftest.py`).

When a system test fails, a full-page screenshot is saved to `reports/screenshots/<test>.png` and the browser console
errors, page errors and failed requests are logged. Logs go to `logs/pytest.log`. Coverage of `climanuvem` is on by
default (`coverage.xml`).

### Real image-analysis tests with Ollama

The default deployment starts the backend with `DISABLE_WORKER=true`, so `pytest` skips the real image-analysis suite
and does not require Ollama. To exercise the full flow, start the optional Ollama services as well:

```bash
WITH_OLLAMA=true bash selenium-java/scripts/sut-compose.sh up --build -d db firebase-emulator ollama ollama-pull backend frontend
REAL_OLLAMA_TESTS=true python -m pytest tests/api/test_image_analysis_system.py
```

The override enables the analysis worker and starts an Ollama container; the model `${OLLAMA_MODEL:-gemma4:e4b}` must
be pulled into it (`docker exec climanuvem_test_ollama ollama pull <model>`). The first run can take longer while the
model downloads. Without `REAL_OLLAMA_TESTS=true`, every test in `test_image_analysis_system.py` is reported as
**skipped**.

### 4 — Tear down

```bash
bash selenium-java/scripts/sut-compose.sh down --volumes
```

---

## API under test

Every endpoint lives under `/api/v1`. The contract (endpoints, status codes and error codes asserted by the suite) is
the same one implemented by `selenium-java`, `cypress-js` and `playwright-csharp`; see the
[API table in the Playwright README](../playwright-csharp/README.md#api-under-test) instead of duplicating it here.

---

## Configuration

System-test accounts are loaded from a CSV file. With the Firebase emulator, `seed-firebase-emulator.sh` creates the
accounts and writes the CSV for you (see Quick start). To create it by hand, start from the template:

```bash
cp tests/resources/accounts.template.csv tests/resources/accounts.local.csv
```

`accounts.local.csv` is ignored by Git:

```csv
role,email,password,verified,description
login_user,user@example.com,secret,true,Existing account for login tests
profile_user,verified-user@example.com,secret,true,Verified account for profile tests
unknown_user,missing@example.test,wrong-password,false,Non-existing account for negative login tests
```

Roles:

- `login_user`: existing account used by the login tests and by the "email already in use" registration case.
- `profile_user`: verified account used by authenticated profile tests. May be the same account as `login_user`.
- `unknown_user`: account expected not to exist, used for negative login attempts.

The login and profile tests run once per `login_user` / `profile_user` row, each in its own isolated browser context.

All settings are plain environment variables, read by `climanuvem/common/config.py`:

| Variable | Default | Description |
|---|---|---|
| `SUT_URL` | `http://localhost:8000` | Backend base URL used by API tests |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend base URL used by system tests |
| `TEST_TOKEN` | `test-token-climanuvem` | Bearer token sent by API tests |
| `HTTP_TIMEOUT_MS` | `10000` | Per-request timeout for API tests |
| `ANALYSIS_TIMEOUT_MS` | `360000` | Maximum wait for real image-analysis completion |
| `ACCOUNTS_FILE` | `tests/resources/accounts.local.csv` | CSV file with system-test accounts |
| `REGISTER_EMAIL_DOMAIN` | `gmail.com` | Domain used for unique registration-test emails |
| `FIREBASE_WEB_API_KEY` | _(unset)_ | Optional Firebase Web API key used to delete the account created by the registration tests |
| `REAL_OLLAMA_TESTS` | `false` | Set `true` (or `1`/`yes`) to enable the real image-analysis tests |
| `PASSWORD_POLICY_ENFORCED` | `false` | Set `true` against a real Firebase project that enforces the uppercase + number password policy; otherwise the password-policy test is skipped (the Auth emulator cannot enforce it) |
| `HEADED` | `false` | Set `1`/`true` to show the browser (default is headless) |
| `PUPPETEER_EXECUTABLE_PATH` | _(system Chrome)_ | Chrome binary to use instead of the system Chrome |
| `BROWSER_ARGS` | _(empty)_ | Extra Chrome flags, space separated |

Read by the bridge only:

| Variable | Effect |
|---|---|
| `NODE_BINARY` | Node executable (default: `node` from the `PATH`) |
| `CI` | Adds `--no-sandbox` to Chrome (needed on Linux CI runners) |
| `USE_SYSTEM_PROXY=1` | Do not force `--no-proxy-server` |

The bridge launches Chrome with `--no-proxy-server`: Windows proxy auto-detection can add 20-30 seconds to every
navigation to `localhost`.

---

## Test architecture

```
bridge/
├── server.mjs               Node JSON-RPC bridge to Puppeteer
├── package.json             Puppeteer pinned to an exact version
└── package-lock.json

climanuvem/
├── browser/                 Python client of the bridge
│   ├── client.py              asyncio JSON-RPC client (spawns node, request ids, deadlines)
│   ├── browser.py             Browser, BrowserContext, Page and Locator
│   ├── testid.py              TestId.of(...) selector builder
│   └── errors.py              BrowserError hierarchy
├── common/
│   ├── config.py              Environment-driven settings
│   ├── api_client.py          REST client (requests): URL builders, uploads, polling helper
│   ├── test_images.py         JPEG fixtures from tests/resources/images + derived invalid payloads
│   ├── test_ids.py            data-testid constants shared with the frontend
│   ├── test_account.py        Account row used by the parameterized system tests
│   └── test_accounts.py       CSV loader and role lookup
└── pages/                   Page Object Model: BasePage + Welcome, Login, Register, Home, Profile and Capture pages

tests/
├── conftest.py              Session-wide browser, isolated page per test, failure screenshots, markers
├── api/                     conftest (ApiClient fixture), assertions (problem+json helper), test_ping, test_auth,
│                            test_analysis, test_cancel, test_delete, test_history, test_image,
│                            test_image_analysis_system (opt-in, real Ollama)
├── e2e/                     conftest (accounts, opened screens, Firebase cleanup), test_login_system,
│                            test_register_system, test_profile_system
├── bridge/                  test_bridge_smoke (local page, no SUT)
└── resources/
    ├── accounts.template.csv   Versioned example for system-test account data
    ├── accounts.local.csv      Local/CI account data, ignored by Git
    └── images/                 tiny.jpg, cloudy.jpg, clear-sky.jpg (checked-in JPEG fixtures)
```

Design notes:

- **Async all the way.** pytest-asyncio runs in auto mode with a single session-wide event loop, so the session-scoped
  browser is shared by every test. Tests are plain `async def` functions; assertions are plain `assert`.
- **Single request path.** Every API call goes through `ApiClient`; polling uses one helper (`poll_until`) with an
  explicit timeout. No hard sleeps.
- **Page objects** extend `BasePage`, locate only through `TestId` and are built with an async factory,
  `await XxxPage.create(page)`, because `__init__` cannot wait.
- **No deprecated APIs.** The suite runs clean with `-W error::DeprecationWarning`.

### UI test conventions

- Page objects and tests locate elements **only by `data-testid`**, through the constants in
  `climanuvem/common/test_ids.py` (mirrors the `testID` props in `sut/frontend`; React Native Web renders them as
  `data-testid`). When a screen changes, add or rename the id in both places.
- The UI under test must run in **English** (`EXPO_PUBLIC_DEFAULT_LANGUAGE=en`, already set by the test compose
  override).
- Previous stack screens stay mounted but hidden, so the same id can exist on several mounted screens. A plain
  `TestId.of(...)` locator targets the first DOM match; scope it with `within(...)` (for example inside a screen's
  `*-feedback` card) or use `nth(...)` when an id is not unique among the mounted screens.
- Timeouts are configured once: the locator default (10 s) and the navigation timeout (30 s) in `climanuvem/browser`.
- The Firebase Auth emulator answers wrong-password / unknown-email more specifically than real Firebase, so the login
  assertions accept both wordings.

## Test mode

The backend is started with `TEST_MODE=true` and `DISABLE_WORKER=true` (see the test override in `selenium-java/scripts`):

- **Any Bearer token is accepted** — API tests send a fixed token; system tests log in against the Firebase Auth
  emulator.
- **Firebase is not initialised against production** — no service account key is needed.
- **Ollama worker is disabled** — analyses stay in `analyzing`, which makes cancel tests deterministic.

---

## Browser API (`climanuvem.browser`)

All methods are `async`. Waiting actions use a default auto-wait timeout of 10 s, set per locator with `with_timeout`.

### `Browser`

| Member | Description |
|---|---|
| `await Browser.launch(headless=True, executable_path=None, args=None, node_binary=None)` | Starts the bridge and Chrome |
| `await browser.new_context()` | Isolated `BrowserContext` (own cookies and storage) |
| `await browser.new_page()` | Page in a fresh context; closing the page closes the context |
| `await browser.close()` | Closes Chrome and the bridge (also via `async with`) |
| `browser.version` | Chrome version string |

### `Page`

| Method | Description |
|---|---|
| `locator(selector, timeout_ms=10000) -> Locator` | Lazy locator for a CSS selector (normally `TestId.of(...)`) |
| `goto(url, timeout_ms=30000)` / `reload(timeout_ms=30000)` | Navigates / reloads and waits for DOMContentLoaded |
| `url()` / `title()` | Current URL / document title |
| `evaluate(script, *args)` | Runs a JS function expression (`"(a, b) => a + b"`) with JSON args and awaits promises |
| `add_init_script(script, *args)` | Runs a JS function expression in every new document before page scripts (mocks, stubs) |
| `press_key(key)` | Presses a key on whatever has focus |
| `set_viewport(width, height)` | Resizes the viewport |
| `clear_storage()` | Clears localStorage, sessionStorage and IndexedDB of the current origin |
| `clear_cookies()` / `cookies()` | Deletes / lists the cookies of the page's context |
| `screenshot(path, full_page=True) -> Path` | Saves a PNG |
| `diagnostics(clear=True)` | Console errors/warnings, page errors and failed requests captured so far |
| `close()` | Closes the page |

### `Locator` (immutable and lazy; Puppeteer auto-waits when an action runs)

| Method | Description |
|---|---|
| `nth(i)` / `first()` / `last()` | The i-th match (0-based, negative counts from the end) |
| `within(selector)` | Matches of a CSS selector below this locator's elements |
| `with_timeout(timeout_ms)` | Same locator with another auto-wait timeout |
| `click()` | Waits for visible, enabled and stable, scrolls into view, clicks |
| `fill(value)` | Clears and sets the value; `""` really clears |
| `type(text, delay_ms=0)` | Types key by key |
| `press(key)` | Focuses the element and presses a key (`"Enter"`) |
| `hover()` / `scroll_into_view()` | Hovers / scrolls the element into view |
| `text()` / `input_value()` | Text content / input value (waits for the element to exist) |
| `attribute(name)` / `property(name)` | DOM attribute / property (for example `checked`) |
| `count()` | Number of current matches (never waits) |
| `is_visible()` / `is_enabled()` | Current state of the first match (never waits) |
| `wait_for(state="visible")` | Waits for `visible`, `hidden`, `attached` or `detached` |

### Errors

`BrowserError` is the base class. `ElementTimeoutError` is a Puppeteer timeout (element, state or navigation).
`BridgeProtocolError` is any other error reported by the bridge (bad selector, JS exception). `BridgeTimeoutError` means
no answer at all. `BridgeCrashedError` means the Node process died and carries its stderr.

---

## CI notes

- The `e2e-puppeteer-python` job in `.github/workflows/ci-cd.yml` mirrors the Playwright job: load the prebuilt images,
  start the SUT with `sut-compose.sh up --detach --no-build db firebase-emulator backend frontend`, wait for
  `/api/v1/ping`, `:5173` and `:9099`, seed the emulator with `ACCOUNTS_FILE` pointing at
  `puppeteer-python/tests/resources/accounts.local.csv`, then `actions/setup-python` (3.12) and `actions/setup-node`
  (22):

  ```bash
  cd puppeteer-python && pip install .
  cd bridge && PUPPETEER_SKIP_DOWNLOAD=true npm ci
  cd .. && CI=true python -m pytest tests --junitxml=results/junit.xml
  ```

- `CI=true` makes the bridge add `--no-sandbox`; the GitHub `ubuntu-latest` runner has Chrome preinstalled, so no
  browser is downloaded.
- The job publishes a test summary (`.github/scripts/junit-summary.py`), uploads `results/`, `reports/` (failure
  screenshots) and `logs/`, and on failure prints the SUT container logs (`sut-compose.sh logs`).
