# CLAUDE.md

Context for Claude Code (and other agentic tools) working in this repo.

## Repository Purpose

`giise2ebench-st-climanuvem` is a **benchmark wrapper repo**: it hosts a system under test (SUT) — ClimaNuvem, imported as-is from [`uo289165/epi-climanuvem`](https://github.com/uo289165/epi-climanuvem) — so an external E2E benchmark can exercise it. All app code lives under [`sut/`](sut/) and is **not authored here**.

```
.
├── docs/                    # formal user requirements consumed by the benchmark, not the SUT
├── sut/                     # System Under Test "ClimaNuvem" (imported as-is)
│   ├── backend/               # FastAPI service
│   ├── frontend/              # Expo / React Native app
│   ├── docs/                  # Sphinx docs source
│   ├── sonar-project.properties
│   └── README.md              # authoritative upstream docs for the SUT
├── .github/
│   ├── workflows/ci-cd.yml  # this wrapper repo's own CI/CD — sut/ has none
│   └── dependabot.yml       # dependency updates for sut/ + this repo's Actions
└── deploy.sh / deploy.ps1   # convenience wrapper to run the SUT locally
```

**Treat `sut/` as vendored** — don't restructure it; keep any fix minimal and aligned with its existing layered conventions (see `sut/README.md`, authoritative for the SUT). Everything at the repo root is bench-repo tooling, free to evolve.

Note: `sut/README.md` describes an upstream CI/docs-publishing setup — that's the *upstream* repo's own CI, not present in the imported `sut/` tree here. This wrapper repo has its own CI/CD and Dependabot config at the root instead, adapted to `sut/backend`/`sut/frontend` paths.

## What Is ClimaNuvem (the SUT)

Mobile app that analyzes cloud photos and generates a short-term local forecast. User signs in (or guest), captures/picks a photo, backend classifies clouds via a multimodal model served by Ollama, result (with optional explainability overlay) is stored and shown in per-user history.

- **Frontend**: Expo/React Native (Expo Router), Firebase Auth (email/Google/guest), camera/gallery, location, FCM push.
- **Backend**: FastAPI, PostgreSQL, Firebase Admin (token verification), async in-process job queue/worker, Ollama client.
- **Formal user requirements**: [`docs/userrequirements_en.txt`](docs/userrequirements_en.txt) / `_es.txt` — reference for benchmark E2E scenarios.
- **E2E system tests**: separate repo, [augustocristian/retorch-st-climanuvem](https://github.com/augustocristian/retorch-st-climanuvem) (RETORCH), not here.

### Main user flow

1. Sign in or continue as guest.
2. App gets a JPG (camera/gallery), optionally with location, FCM token, explainability flag.
3. Backend verifies the Firebase ID token, stores the image, creates an analysis row (`analyzing`).
4. Async worker dequeues, calls Ollama, persists cloud types/forecast/bounding boxes.
5. Backend push-notifies on finish/fail (if FCM token given).
6. App reads history, renders results/warnings/bounding boxes.

### Backend (`sut/backend/app/`)

Layered: `presentation/` (routes, `test_routes.py` only when `TEST_MODE=true`, Firebase bearer-token auth dependency) → `business/` (`analysis_service.py`, `auth_service.py`, `worker.py`'s `analysis_worker` loop) → `data/` (`analysis_repository.py` over SQLAlchemy) → `infrastructure/` (`config.py`'s `Settings`/`get_settings()`, DB engine/session/bootstrap/Alembic migrations, `firebase_service.py`, `ollama_client.py`, `queue.py`, `prompts/*.j2`). `main.py` is the FastAPI app factory (lifespan bootstraps DB + worker, `DISABLE_WORKER` to opt out; mounts `/uploads`, CORS from `CORS_ALLOW_ORIGINS`, `GET /ping`/`GET /`).

Tests in `sut/backend/tests/` (pytest, one file per module). Managed with [Poetry](https://python-poetry.org/) (`pyproject.toml` + `poetry.lock`); run `poetry run pytest` from `sut/backend/`; config under `[tool.pytest.ini_options]`; coverage → `coverage.xml` (SonarCloud).

### Frontend (`sut/frontend/`)

Expo Router, views/controllers/services split: `app/` (route files, thin, excluded from coverage), `src/views/` + `src/controllers/` (excluded from coverage), `src/services/` (Firebase/API/notifications/storage — most unit-tested; `AuthService.ts`/`LoggerService.ts`/`NotificationService.ts`/`mockData.ts` excluded as thin adapters), `src/hooks/`+`hooks/` (shared hooks, `.web.ts` variants), `src/models/`/`src/config/`/`src/styles/` (excluded, static), `components/` (themed UI primitives), `android/` (native Gradle project for release APKs).

Tests in `__tests__/` (Jest + `jest-expo`). `npm test` / `npm run test:coverage` (→ `coverage/lcov.info`) / `npm run lint` (`expo lint`).

## Local Deployment

Authoritative instructions: [`sut/README.md`](sut/README.md#local-deployment). Summary:

- **Backend**: `sut/backend/.env` (`POSTGRES_*`, `OLLAMA_MODEL` for Compose; or `DATABASE_URL`, `FIREBASE_KEY_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`, `CORS_ALLOW_ORIGINS`, `LOG_LEVEL`, `TEST_MODE`, `DISABLE_WORKER` for manual) + `sut/backend/secrets/firebase_key.json` (never commit).
- **Frontend**: `sut/frontend/.env` (`EXPO_PUBLIC_BACKEND_URL`, `EXPO_PUBLIC_TEST_MODE`, `EXPO_PUBLIC_DEFAULT_LANGUAGE`, `EXPO_PUBLIC_FIREBASE_*`) + `sut/frontend/google-services.json` (never commit).

Root convenience scripts (`deploy.sh` / `deploy.ps1`) just wrap the documented Docker Compose / npm commands:

```bash
./deploy.sh backend        # docker compose up --build (Postgres + Ollama + FastAPI)
./deploy.sh frontend       # npm install && npm start (Expo dev server)
./deploy.sh all            # backend detached, then frontend foreground
./deploy.sh down [--volumes]
```
PowerShell: same subcommands via `./deploy.ps1`, `-Volumes` flag.

Fails fast if `sut/backend/.env` is missing; warns (non-fatal) if the Firebase key or frontend `.env` are missing.

## Tests And Quality

```bash
cd sut/backend && poetry install --with test && poetry run pytest
cd sut/frontend && npm test && npm run test:coverage && npm run lint
```

SonarCloud reads `sut/backend/coverage.xml` + `sut/frontend/coverage/lcov.info` (see `sut/sonar-project.properties`); coverage exclusions documented in `sut/README.md`.

## CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml), adapted from upstream but pointed at `sut/backend`/`sut/frontend`. Triggers: `pull_request`, `push` (any branch), `workflow_dispatch` (`build_android` input). Jobs:

1. **`changes`** — `dorny/paths-filter` on `sut/backend/**`/`sut/frontend/**`; `workflow_dispatch` treats both as changed.
2. **`backend-tests`** — Python 3.12, Poetry (`snok/install-poetry`, in-project `.venv`), `poetry install --with test`, `poetry run pytest`, archives `sut/backend/logs/*`.
3. **`frontend-tests`** — Node 22, restores `google-services.json` from `GOOGLE_SERVICES_JSON_BASE64` if present, `npm ci`, `npm run lint`, `npm test`.
4. **`sonarcloud`** — regenerates both coverage reports, runs `SonarSource/sonarqube-scan-action` with `projectBaseDir: sut`. Needs `SONAR_TOKEN`. Skips when `github.actor == 'dependabot[bot]'` (see Dependabot section).
5. **`deploy-docs`** — only on push to `main`/tag. `poetry install --with docs`, builds Sphinx via the in-project venv (`working-directory: sut`), publishes to GitHub Pages (needs `github-pages` environment).
6. **`android-release-apk`** — on `frontend/` change to `main`, or manual dispatch with `build_android=true`. Restores keystore + `google-services.json` from secrets, writes `MYAPP_UPLOAD_*` Gradle props, `./gradlew assembleRelease`, publishes APK as artifact + GitHub Release (`frontend-v1.0.0-<run_number>`).
7. **`e2e-*`** (selenium-java, playwright-csharp, cypress-javascript, puppeteer-python) — **placeholders** only (checkout + TODO echo), run unconditionally so stage names are visible. Implementing one needs its toolchain setup, a way to stand up the SUT (reuse `./deploy.sh`), and removing the placeholder step.

Secrets: `SONAR_TOKEN`; `GOOGLE_SERVICES_JSON_BASE64` (optional for 3–4, required for 6); `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`; `EXPO_PUBLIC_*` (all only for step 6). Same names/purposes as upstream — see [`sut/README.md`](sut/README.md#cicd).

## Dependabot

[`.github/dependabot.yml`](.github/dependabot.yml): `pip` (`/sut/backend`), `npm` (`/sut/frontend`), `docker` (one entry each for backend/frontend `Dockerfile`), `github-actions` (`/`). Weekly.

`groups` is used **only for genuine version-lockstep siblings** (bumping one alone breaks the build) — not to bucket by theme. One PR per package otherwise:

- **`pip`**: `fastapi-pydantic`, `firebase-google-cloud`, `sqlalchemy` (+alembic), `http-stack` (httpx/httpcore/h2/hpack/hyperframe/anyio). `pytest*` (Poetry `test` group) and `sphinx*` (`docs` group) ungrouped, own PRs each.
- **`npm`**: `expo-sdk` (expo, `expo-*`, `@expo/*`, react, react-dom, react-native, `react-native-*`, `@types/react`, jest, jest-expo — `expo install` bumps these as one unit), `react-navigation` (`@react-navigation/*`), `testing` (`@types/jest`), `linting` (eslint, `eslint-*`, `@typescript-eslint/*`, typescript).
- **`github-actions`**: ungrouped, no cross-action version constraints.
- **`docker`**: ungrouped, one `FROM` each.

**Ignore rules and why:**
- `pip`: none currently. (A `sphinx <8.2.0` cap existed while `backend-tests` ran Python 3.10 — Sphinx 8.2+/9.x need ≥3.11/≥3.12; removed once CI moved to Python 3.12.)
- `npm` `eslint`: `semver-major` ignored — `eslint-config-expo` still bundles plugins that break under ESLint 10's flat-config API.
- `npm` `react`/`react-dom`/`react-native`/`react-native-*`/`@types/react`/`jest`/`jest-expo`: `semver-major`+`semver-minor` ignored. `npm` `expo`/`expo-*`/`@expo/*`: `semver-major` ignored. **Why**: grouping only guarantees these land in one PR, not that the combo matches what Expo's `bundledNativeModules.json` supports for the pinned `expo` version — this broke CI twice via ordinary minor bumps (jest-expo on the wrong SDK track; react-native 0.87.1 vs SDK 57's pinned 0.86.3). Patches still auto-update; bump the full set by hand with `npx expo install --fix` when moving SDKs.

Note: `pydantic`/`pydantic_core` also once landed out of sync despite matching the `fastapi-pydantic` group — that came from the separate tool that combines multiple Dependabot PRs into one branch, not from dependabot.yml, and isn't fixable here.

When bumping by hand, respect the same lockstep sets (e.g. don't bump one `expo-*` package alone; don't bump `fastapi` without checking `starlette`).

**Commit messages / labels**: no block sets `include: "scope"` (it would append a redundant `(deps)`/`(deps-dev)` suffix on top of the already-descriptive `prefix`). `npm` and `pip` both set `prefix-development` (`chore(frontend dev-deps)` / `chore(backend dev-deps)`) since both manifests expose a real dev/prod split Dependabot can see (`package.json` deps/devDeps; Poetry's `[project.dependencies]` vs. optional `test`/`docs` groups — only possible for `pip` since the Poetry migration). Every block sets `assignees: [augustocristian]` and labels (must pre-exist in the repo: `backend`, `backend-ai`, `frontend`, `docker`, `actions` — Dependabot won't create them):

| Block | Labels |
| --- | --- |
| `pip` | `backend`, `backend-ai` |
| `npm` | `frontend` |
| `docker` (backend) | `backend`, `docker` |
| `docker` (frontend) | `frontend`, `docker` |
| `github-actions` | `actions` |

`rebase-strategy: "disabled"` everywhere — stops auto-rebase from re-triggering CI (incl. `sonarcloud`) on every `main` push while a PR waits for review. `ci-cd.yml`'s `sonarcloud` job also guards `if: github.actor != 'dependabot[bot]'`, so individual Dependabot PRs skip it entirely — but that guard is keyed on the triggering actor, so a manually-combined "Combined dependency updates" branch (pushed by a human) still runs it.

**Known gap**: `sut/sonar-project.properties` still has the *upstream* project's `sonar.projectKey`/`sonar.organization` (`uo289165_epi-climanuvem` / `uo289165-1`), so every `sonarcloud` run fails "Not authorized or project not found" until repointed at a project this repo's `SONAR_TOKEN` can access. Pre-existing, unrelated to dependency versions.

## Conventions For This Repo

- **`.gitignore`**: root covers IDE/OS cruft only; `sut/backend/.gitignore` / `sut/frontend/.gitignore` remain source of truth for stack-specific ignores — don't duplicate.
- **Secrets**: never commit `.env`, `firebase_key.json`, `google-services.json`, keystores (already gitignored).
- **Don't restructure `sut/`** casually — vendored from upstream.
- **Formal requirements** in `docs/*.txt` are the reference for benchmark E2E scenario coverage.
- **CI/Dependabot paths** hardcode `sut/backend`/`sut/frontend` — re-check both files if `sut/` is ever restructured or re-vendored.
