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
│   ├── docs/                 # Sphinx technical docs (SUT's own, auto-published to GitHub Pages)
│   ├── images/               # architecture diagrams + UI screenshots used in sut/README.md
│   ├── sonar-project.properties
│   ├── CITATION.cff
│   └── README.md             # full upstream documentation for ClimaNuvem (authoritative for the SUT)
├── .gitignore               # root-level ignores (IDE noise + generic project rubbish)
└── deploy.sh / deploy.ps1   # convenience wrapper to stand up (and tear down) the SUT locally
```

**When making changes:** treat `sut/` as a vendored/imported tree. Prefer not to restructure it; if the SUT itself needs a fix, keep the change minimal and consistent with its existing conventions (see `sut/README.md`, which is the authoritative and very detailed source of truth for that application). Everything at the repo root (this file, `.gitignore`, `deploy.*`, `stop.*`, `docs/`) is bench-repo tooling and is fair game to evolve freely.

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

Defined upstream in the SUT's own `.github/workflows/ci-cd.yml` (part of the imported `sut/` tree, not this wrapper repo's CI). It runs backend `pytest` and frontend `lint`/`test` by changed path, reports coverage to SonarCloud, and — on `frontend/` changes on `main` — builds and publishes a signed Android release APK to GitHub Releases. See [`sut/README.md`](sut/README.md#cicd) for required secrets.

## Conventions For This Repo

- **`.gitignore`**: the root `.gitignore` targets IDE/OS rubbish (JetBrains `.idea/`/`.iml`, Eclipse `.project`/`.classpath`/`.settings/`, VS Code `.vscode/*` with the useful shared files re-allowed, plus OS cruft) so no editor metadata gets committed regardless of which IDE a contributor uses. `sut/backend/.gitignore` and `sut/frontend/.gitignore` remain the source of truth for stack-specific ignores (Python venvs, `node_modules/`, Expo/Android build artifacts, secrets, `.env` files) — don't duplicate those at the root, only cover what they don't.
- **Secrets**: never commit `.env` files, `firebase_key.json`, `google-services.json`, Android keystores, or any other credential. These are already covered by `.gitignore` at the appropriate level.
- **Don't restructure `sut/`** casually — it tracks an upstream project. If you need to patch it, keep the diff minimal and aligned with its existing layered architecture (presentation/business/data/infrastructure on the backend; views/controllers/services on the frontend).
- **Formal requirements** in `docs/*.txt` describe expected user-facing behavior (auth, registration, upload, analysis, forecasting, warnings, cancellation, history, explainability) and are the reference for what the benchmark's E2E scenarios should cover.
