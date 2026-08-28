# CLAUDE.md

This file gives Claude Code (and other agentic tools) the context needed to work effectively in this repository.

## Repository Purpose

`giise2ebench-st-climanuvem` is a **benchmark wrapper repository**. Its job is to host a "system under test" (SUT) — an existing, independently-developed application — so it can be exercised by an external end-to-end testing benchmark/harness. The actual application code lives entirely under [`sut/`](sut/) and was imported from its own upstream repository ([`uo289165/epi-climanuvem`](https://github.com/uo289165/epi-climanuvem)); it is **not authored in this repo**.

```
.
├── README.md              # one-line placeholder for the wrapper repo itself
├── docs/                   # formal user requirements consumed by the benchmark, not by the SUT
│   ├── userrequirements_en.txt
│   └── userrequirements_es.txt
├── sut/                    # the System Under Test: "ClimaNuvem" (imported as-is)
│   ├── backend/             # FastAPI service
│   ├── frontend/            # Expo / React Native app
│   ├── docs/                 # Sphinx technical docs (source only — see CI/CD below for publishing)
│   ├── images/               # architecture diagrams + UI screenshots used in sut/README.md
│   ├── sonar-project.properties
│   ├── CITATION.cff
│   └── README.md             # full upstream documentation for ClimaNuvem (authoritative for the SUT)
├── .github/
│   ├── workflows/ci-cd.yml # this wrapper repo's own CI/CD (see CI/CD below) — sut/ has none of its own
│   └── dependabot.yml       # dependency update config for both sut/ ecosystems + this repo's Actions
├── .gitignore               # root-level ignores (IDE noise + generic project rubbish)
└── deploy.sh / deploy.ps1   # convenience wrapper to stand up (and tear down) the SUT locally
```

**When making changes:** treat `sut/` as a vendored/imported tree. Prefer not to restructure it; if the SUT itself needs a fix, keep the change minimal and consistent with its existing conventions (see `sut/README.md`, which is the authoritative and very detailed source of truth for that application). Everything at the repo root (this file, `.gitignore`, `deploy.*`, `.github/`, `docs/`) is bench-repo tooling and is fair game to evolve freely.

Note: `sut/README.md` describes a `.github/workflows/ci-cd.yml` and auto-published Sphinx docs as part of upstream ClimaNuvem — that refers to the *upstream* `uo289165/epi-climanuvem` repository's own CI. The imported `sut/` tree in this repo does **not** include a `.github/` directory, so this wrapper repo has its own CI/CD and Dependabot config at the root instead (see below), adapted to the `sut/backend` / `sut/frontend` paths used here.

## What Is ClimaNuvem (the SUT)

ClimaNuvem is a mobile application for analyzing cloud photographs and generating a short-term local weather forecast from the detected cloud types. A user signs in (or continues as a guest), captures or picks a photo, the backend classifies the clouds with a multimodal model served by Ollama, and the result — including an optional explainability overlay — is stored and shown in a per-user history.

Stack:
- **Frontend**: Expo / React Native app (Expo Router), Firebase Auth (email, Google, guest), camera/gallery access, location, Firebase Cloud Messaging push notifications.
- **Backend**: FastAPI, PostgreSQL persistence, Firebase Admin (token verification), an asynchronous in-process job queue/worker, and an Ollama client for cloud classification.
- **Formal user requirements** (used by the benchmark to derive test scenarios) live in [`docs/userrequirements_en.txt`](docs/userrequirements_en.txt) and [`docs/userrequirements_es.txt`](docs/userrequirements_es.txt).
- **E2E system tests** for this SUT are maintained in a separate repository: [augustocristian/retorch-st-climanuvem](https://github.com/augustocristian/retorch-st-climanuvem) (RETORCH framework), not in this repo.

### Main user flow

1. User signs in or enters as a guest.
2. App obtains a JPG image (camera or gallery), optionally attaching location, an FCM token, and an explainability flag.
3. Backend verifies the Firebase ID token, stores the image, and creates an analysis row in `analyzing` state.
4. An async worker picks the job off the queue, calls Ollama with a multimodal prompt, and persists cloud types / forecast / bounding boxes to PostgreSQL.
5. Backend sends a push notification (if an FCM token was supplied) when the analysis finishes or fails.
6. App polls/reads history and renders results, weather warnings, and bounding boxes when available.

### Backend architecture (`sut/backend/app/`)

Layered design:
- **`presentation/`** — HTTP surface. `routes/analysis_routes.py` (mounted at `/analysis`) exposes upload, status/history, cancel, and delete endpoints; `routes/test_routes.py` is a test-only router enabled solely when `TEST_MODE=true`. `dependencies/auth_dependency.py` verifies the Firebase bearer token (or accepts the configured `TEST_TOKEN` in test mode) and injects the current user.
- **`business/`** — use cases. `analysis_service.py` orchestrates creating/cancelling/deleting analyses; `auth_service.py` wraps auth logic; `worker.py` (`analysis_worker`) is the long-running asyncio task that drains the queue, calls Ollama, and writes results.
- **`data/`** — `analysis_repository.py`, the persistence layer over SQLAlchemy models/queries.
- **`infrastructure/`** — cross-cutting adapters: `config.py` (env-driven `Settings` singleton via `get_settings()`), `database/` (SQLAlchemy engine/session, `bootstrap.py` which creates tables and seeds the cloud catalog on startup, Alembic `migrations/`, raw `create_tables.sql` / `seed_clouds.sql`), `firebase_service.py` (Firebase Admin token verification), `ollama_client.py` (HTTP client to the Ollama `/api/generate` endpoint), `queue.py` (the async job queue), `logging_config.py`, and `prompts/` (Jinja2 templates `classifier_simple.j2`, `explainer.j2` used to build the Ollama prompts).
- **`main.py`** — FastAPI app factory. Lifespan hook bootstraps the DB and starts/stops the worker task (`DISABLE_WORKER` to opt out). Mounts `/uploads` as static files, applies CORS from `CORS_ALLOW_ORIGINS`, and exposes `GET /ping` and `GET /` health/info endpoints.

Tests live in `sut/backend/tests/` (pytest, one file per module — repository, routes, services, worker, auth, firebase, ollama client, database bootstrap/session). Run with `pytest` from `sut/backend/`; config in `pytest.ini`; coverage written to `coverage.xml` (consumed by SonarCloud).

### Frontend architecture (`sut/frontend/`)

Expo Router app with a views/controllers/services split:
- **`app/`** — Expo Router route files (`index.tsx`, `login.tsx`, `register.tsx`, `home.tsx`, `capture.tsx`, `profile.tsx`, `_layout.tsx`). Excluded from coverage (thin routing wrappers).
- **`src/views/`** — presentational screens/components rendering UI and emitting events. Excluded from coverage.
- **`src/controllers/`** — coordinate state and navigation between views and services. Excluded from coverage.
- **`src/services/`** — encapsulate Firebase auth, the backend API client, notifications, and local preference storage. Most are unit-tested (see `__tests__/`); `AuthService.ts`, `LoggerService.ts`, `NotificationService.ts`, and `mockData.ts` are excluded from coverage as thin native/Firebase adapters.
- **`src/hooks/`**, **`hooks/`** — shared React hooks (e.g. `useAnalysisHistory`, `useNotificationResponse`, theming hooks). `hooks/` (top-level) has `.web.ts` platform variants for web-specific behavior.
- **`src/models/`**, **`src/config/`**, **`src/styles/`** — types, configuration constants, and styling. Excluded from coverage (static/config data).
- **`src/i18n.ts`** — i18next setup; locale files under `src/locales/**` (or similar) are excluded from coverage as static data.
- **`components/`** — small reusable/themed UI primitives (`themed-text.tsx`, `themed-view.tsx`, `ui/`).
- **`android/`** — native Android project (Gradle) generated/maintained for building release APKs; has its own `.gitignore`.
- Tests in `__tests__/` (Jest + `jest-expo`), config in `jest.config.js` / `jest.setup.js`. Run with `npm test`; coverage via `npm run test:coverage` writes `coverage/lcov.info` (consumed by SonarCloud). Lint via `npm run lint` (`expo lint` / ESLint, config in `eslint.config.js`).

## Local Deployment

Full, authoritative instructions (including all environment variables and Firebase setup) are in [`sut/README.md`](sut/README.md#local-deployment). Summary:

**Backend** needs `sut/backend/.env` (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `OLLAMA_MODEL` for Docker Compose; or `DATABASE_URL`, `FIREBASE_KEY_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`, `CORS_ALLOW_ORIGINS`, `LOG_LEVEL`, `TEST_MODE`, `DISABLE_WORKER` for a manual run) plus a Firebase Admin credentials file at `sut/backend/secrets/firebase_key.json` (never commit this).

**Frontend** needs `sut/frontend/.env` (`EXPO_PUBLIC_BACKEND_URL`, `EXPO_PUBLIC_TEST_MODE`, `EXPO_PUBLIC_DEFAULT_LANGUAGE`, and the `EXPO_PUBLIC_FIREBASE_*` client keys) plus `sut/frontend/google-services.json` for Android (never commit this either).

### Root-level convenience scripts

This wrapper repo adds a thin deployment script at the root (both Bash and PowerShell — pick whichever matches your shell) that just calls the documented Docker Compose / npm commands in `sut/backend` and `sut/frontend`; it doesn't replace or reinterpret the SUT's own setup:

```bash
# Bash (Linux/macOS/WSL/Git Bash)
./deploy.sh backend        # docker compose up --build in sut/backend (Postgres + Ollama + FastAPI)
./deploy.sh frontend       # npm install && npm start in sut/frontend (Expo dev server)
./deploy.sh all            # backend detached, then frontend in the foreground
./deploy.sh down           # docker compose down for the backend
./deploy.sh down --volumes # also wipes Postgres data + Ollama models
```

```powershell
# PowerShell (Windows)
./deploy.ps1 backend
./deploy.ps1 frontend
./deploy.ps1 all
./deploy.ps1 down
./deploy.ps1 down -Volumes   # also wipes Postgres data + Ollama models
```

The script fails fast with a clear message if `sut/backend/.env` is missing, and warns (non-fatal) if `sut/backend/secrets/firebase_key.json` or `sut/frontend/.env` are missing, since the app will still start but auth/config will not work correctly.

## Tests And Quality

```bash
# Backend
cd sut/backend
pip install -r requirements.txt -r requirements-dev.txt
pytest

# Frontend
cd sut/frontend
npm test
npm run test:coverage
npm run lint
```

SonarCloud analysis (`sut/sonar-project.properties`) reads `sut/backend/coverage.xml` and `sut/frontend/coverage/lcov.info`; see `sut/README.md` for the full list of paths excluded from coverage and why.

## CI/CD

This wrapper repo defines its own workflow at [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml), adapted from ClimaNuvem's upstream pipeline but pointed at `sut/backend` and `sut/frontend`. Triggers: `pull_request`, `push` (any branch), and `workflow_dispatch` (with a `build_android` boolean input to force an APK build). Stages:

1. **`changes`** — `dorny/paths-filter` diffs `sut/backend/**` and `sut/frontend/**` to decide which downstream jobs run; a manual `workflow_dispatch` run always treats both as changed.
2. **`backend-tests`** (needs `changes`, runs iff backend changed) — Python 3.10, installs `sut/backend/requirements.txt` + `requirements-dev.txt`, runs `pytest`.
3. **`frontend-tests`** (needs `changes`, runs iff frontend changed) — Node 22, restores `google-services.json` from the `GOOGLE_SERVICES_JSON_BASE64` secret when present (lint/test proceed without it otherwise), `npm ci`, `npm run lint`, `npm test`.
4. **`sonarcloud`** (needs `changes`, runs iff either side changed or on manual dispatch) — regenerates backend (`pytest`, writing `coverage.xml`) and frontend (`npm run test:coverage`, writing `coverage/lcov.info`) coverage, then runs `SonarSource/sonarqube-scan-action` with `projectBaseDir: sut` so it picks up [`sut/sonar-project.properties`](sut/sonar-project.properties) (whose paths are relative to `sut/`). Requires the `SONAR_TOKEN` secret.
5. **`deploy-docs`** — only on `push` to `main` or a tag. Builds the Sphinx docs (`sphinx-build -b html docs docs/_build/html`, run with `working-directory: sut` so `sut/docs/conf.py`'s `../backend` import path resolves) and publishes `sut/docs/_build/html` to GitHub Pages via `actions/upload-pages-artifact` + `actions/deploy-pages` (needs the `github-pages` environment enabled in repo settings).
6. **`android-release-apk`** (needs `changes` + `frontend-tests`) — runs when `frontend/` changed on a `main` push, or when manually dispatched with `build_android=true`. Validates all required secrets are present first, restores the release keystore and `google-services.json` from base64 secrets, writes `MYAPP_UPLOAD_*` Gradle properties (matching the signing config already wired into [`sut/frontend/android/app/build.gradle`](sut/frontend/android/app/build.gradle)), runs `./gradlew assembleRelease`, and publishes the signed APK as both a workflow artifact and a GitHub Release tagged `frontend-v1.0.0-<run_number>`.
7. **`e2e-selenium-java`**, **`e2e-playwright-csharp`**, **`e2e-cypress-javascript`**, **`e2e-puppeteer-python`** — **placeholders**, one per E2E benchmark tool/language combination. Each currently only checks out the repo and echoes a `TODO`; none stand up the SUT or run a real suite yet. They run unconditionally (no `needs`/`if` gating) so the stage names are visible in the Actions UI as the benchmark grows. When implementing one, give it the toolchain setup it actually needs (e.g. `actions/setup-java` + Maven/Gradle for Selenium, `actions/setup-dotnet` for Playwright, `actions/setup-node` for Cypress, `actions/setup-python` for Puppeteer), a way to stand up the SUT (likely reusing `./deploy.sh backend`/`./deploy.sh frontend` or a dedicated CI-only compose profile), and remove the placeholder `Placeholder` step.

Required repository secrets: `SONAR_TOKEN`; `GOOGLE_SERVICES_JSON_BASE64` (optional for steps 3–4, required for step 6); `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`; and the `EXPO_PUBLIC_*` Firebase/backend-URL values, all only needed for step 6. See [`sut/README.md`](sut/README.md#cicd) for what each one is for — the secret *names* and *purposes* are unchanged from upstream, only the file paths inside the jobs differ.

## Dependabot

[`.github/dependabot.yml`](.github/dependabot.yml) covers every ecosystem in the repo: `pip` (`/sut/backend`), `npm` (`/sut/frontend`), `docker` (`/sut/backend` and `/sut/frontend`, one entry each for their `Dockerfile`), and `github-actions` (`/`, since workflow files always live at the repo root regardless of where the code they build lives). All run on a weekly schedule.

Several dependencies in this stack are only safe to upgrade as a set — bumping one without its siblings breaks compatibility until the rest catch up — so each ecosystem defines `groups` to bundle them into a single PR instead of one PR per package:

- **`pip` (`sut/backend`)**: `fastapi-pydantic` (fastapi + starlette + the pydantic v2 family), `firebase-google-cloud` (firebase_admin + the whole `google-*`/`grpcio`/`protobuf` tree it depends on), `sqlalchemy` (sqlalchemy + alembic), `http-stack` (httpx + httpcore + h2/hpack/hyperframe + anyio), plus `pytest` and `sphinx` groups for the dev dependencies.
- **`npm` (`sut/frontend`)**: `expo-sdk` — the big one — groups `expo`, every `expo-*`/`@expo/*` package, `react`, `react-dom`, `react-native`, and every `react-native-*` package (reanimated, gesture-handler, safe-area-context, screens, worklets, web) plus `@types/react`, because the Expo SDK pins a single compatible version set across all of these and `expo install` always bumps them together — letting Dependabot open them as separate PRs would leave the tree in a broken, half-upgraded state between merges. Also `react-navigation` (`@react-navigation/*`, released as a suite), `testing` (`jest`/`jest-expo`/`@types/jest`), and `linting` (`eslint`/`eslint-config-expo`).
- **`github-actions` (`/`)**: an `actions` group for first-party `actions/*` actions (checkout, setup-python, setup-node, setup-java, upload-artifact, upload-pages-artifact, deploy-pages). The SHA-pinned third-party actions (`dorny/paths-filter`, `SonarSource/sonarqube-scan-action`, `softprops/action-gh-release`) are left ungrouped so their pin bumps get individual review.
- **`docker`**: no groups — each Dockerfile has a single `FROM` base image, so there are no siblings to bundle.

When touching dependency versions by hand (not via Dependabot), keep the same "move together" sets in mind — e.g. don't bump a single `expo-*` package without checking it against the Expo SDK version, and don't bump `fastapi` without checking its `starlette` pin.

Every update block also sets `assignees: [augustocristian]` and per-ecosystem `labels`, applied to every PR that block opens (Dependabot doesn't support per-group labels, only per-block, which is why the `backend-ai` label below lands on *all* `sut/backend` pip PRs rather than a narrower subset — there's no pip dependency that's cleanly "AI-only" in this stack anyway, since the classification model is called over plain HTTP to Ollama rather than through a pip-installed client):

| Update block | Labels |
| --- | --- |
| `pip` (`/sut/backend`) | `backend`, `backend-ai` |
| `npm` (`/sut/frontend`) | `frontend` |
| `docker` (`/sut/backend`) | `backend`, `docker` |
| `docker` (`/sut/frontend`) | `frontend`, `docker` |
| `github-actions` (`/`) | `actions` |

**Labels must already exist in the GitHub repo** — Dependabot does not create missing labels, it silently skips applying ones that aren't there. Before this config takes effect, create `backend`, `backend-ai`, `frontend`, `docker`, and `actions` as repository labels (Settings → Labels, or `gh label create`).

## Conventions For This Repo

- **`.gitignore`**: the root `.gitignore` targets IDE/OS rubbish (JetBrains `.idea/`/`.iml`, Eclipse `.project`/`.classpath`/`.settings/`, VS Code `.vscode/*` with the useful shared files re-allowed, plus OS cruft) so no editor metadata gets committed regardless of which IDE a contributor uses. `sut/backend/.gitignore` and `sut/frontend/.gitignore` remain the source of truth for stack-specific ignores (Python venvs, `node_modules/`, Expo/Android build artifacts, secrets, `.env` files) — don't duplicate those at the root, only cover what they don't.
- **Secrets**: never commit `.env` files, `firebase_key.json`, `google-services.json`, Android keystores, or any other credential. These are already covered by `.gitignore` at the appropriate level.
- **Don't restructure `sut/`** casually — it tracks an upstream project. If you need to patch it, keep the diff minimal and aligned with its existing layered architecture (presentation/business/data/infrastructure on the backend; views/controllers/services on the frontend).
- **Formal requirements** in `docs/*.txt` describe expected user-facing behavior (auth, registration, upload, analysis, forecasting, warnings, cancellation, history, explainability) and are the reference for what the benchmark's E2E scenarios should cover.
- **CI/Dependabot paths**: both [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) and [`.github/dependabot.yml`](.github/dependabot.yml) hardcode the `sut/backend` / `sut/frontend` prefixes. If `sut/` is ever restructured (it shouldn't be casually, per above) or the SUT is re-vendored from a newer upstream snapshot, re-check both files against the actual paths and dependency manifests rather than assuming they still match.
