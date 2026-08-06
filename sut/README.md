# ClimaNuvem

[![CI/CD](https://github.com/uo289165/epi-climanuvem/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/uo289165/epi-climanuvem/actions/workflows/ci-cd.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=uo289165_epi-climanuvem&metric=alert_status)](https://sonarcloud.io/summary/overall?id=uo289165_epi-climanuvem)
[![Documentation](https://img.shields.io/badge/docs-Sphinx-blue?logo=readthedocs&logoColor=white)](https://urianf.github.io/epi-climanuvem/)

ClimaNuvem is a mobile application for analyzing cloud photographs and generating a short-term local weather forecast based on the detected cloud types. Users can sign in or continue as guests, take a picture or select one from the gallery, send it to the backend, classify the clouds with a multimodal model served by Ollama, and review previous analyses from the mobile app.

The project combines an Expo/React Native app, a FastAPI backend, Firebase authentication, Firebase Cloud Messaging push notifications, PostgreSQL persistence, and asynchronous analysis processing.

## Contents

- [What Is ClimaNuvem](#what-is-climanuvem)
- [User Requirements](#user-requirements)
- [Technical Documentation](#technical-documentation)
- [Application UI](#application-ui)
- [Architecture](#architecture)
- [Local Deployment](#local-deployment)
- [APK Installation](#apk-installation)
- [Tests And Quality](#tests-and-quality)
- [CI/CD](#cicd)
- [Contributing](#contributing)
- [How To Cite](#how-to-cite)

## What Is ClimaNuvem

ClimaNuvem is designed as a support tool for identifying clouds from a mobile device and relating them to possible near-term weather changes. Users can upload an image, attach location data, receive the result when the analysis finishes, and review past analyses from the history view.

Main features:

- Firebase authentication, including email, Google sign-in, and guest mode.
- Camera capture or gallery image selection.
- JPG image uploads up to 5 MB.
- Optional location and coordinate registration for each analysis.
- Asynchronous backend analysis through a job queue.
- Cloud type classification with a local multimodal model served by Ollama.
- Optional explainability through bounding boxes over the analyzed image.
- Per-user analysis history.
- Cancellation of analyses in progress.
- Deletion of individual analyses and user data.
- Push notifications when an analysis finishes or fails.
- Spanish/English language support and light/dark/system theme modes.

## User Requirements

The formal user requirements for ClimaNuvem are documented in the `docs/` directory in both supported languages:

- [`docs/userrequirements_en.txt`](docs/userrequirements_en.txt): English version.
- [`docs/userrequirements_es.txt`](docs/userrequirements_es.txt): Spanish version.

These documents describe the expected user-facing behavior of the application, including authentication, registration, image upload, cloud analysis, weather forecasting, risk warnings, analysis cancellation, history access, and explainability results.

## Technical Documentation

The technical documentation of the backend is auto-generated with **Sphinx** from the `docs/` directory and deployed automatically to GitHub Pages by the CI pipeline on every push to `main` and on version tags:

- **Technical documentation (API Reference)**: [https://urianf.github.io/epi-climanuvem/](https://urianf.github.io/epi-climanuvem/)

To build it locally:

```bash
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
sphinx-build -b html docs docs/_build/html
```

## Application UI

| Welcome                                                                       | Sign In                                                          | Register                                                                     | Home                                                                            |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| <img src="images/ui-welcome.jpg" alt="ClimaNuvem welcome screen" width="180"> | <img src="images/ui-login.jpg" alt="Sign-in screen" width="180"> | <img src="images/ui-register.jpg" alt="Account creation screen" width="180"> | <img src="images/ui-home.jpg" alt="Home screen with quick actions" width="180"> |

| Profile And Settings                                                                                               | Image Upload                                                                                                                       | History                                                                       | Results                                                                                                |
| ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| <img src="images/ui-profile-settings.jpg" alt="Profile, theme, language, and account deletion screen" width="180"> | <img src="images/ui-analysis-upload.jpg" alt="Screen to take a photo, select from gallery, and enable explainability" width="180"> | <img src="images/ui-history.jpg" alt="Previous analysis history" width="180"> | <img src="images/ui-analysis-results.jpg" alt="Analysis detail with detected cloud types" width="180"> |

## Architecture

The project is split into two main applications:

- `frontend/`: Expo/React Native app with Expo Router, Firebase Auth, camera, gallery, location, notifications, and analysis history.
- `backend/`: FastAPI API with PostgreSQL, Firebase Admin, asynchronous analysis queue, and Ollama client.

### General View

![General architecture diagram](images/architecture-general.png)

Main flow:

1. The user signs in or enters as a guest.
2. The app obtains a JPG image from the camera or gallery.
3. Location, FCM token, and explainability settings are optionally attached.
4. The backend verifies the Firebase token, stores the image, and creates an analysis in `analyzing` state.
5. A worker processes the queue, calls Ollama, and persists the results in PostgreSQL.
6. The backend sends a push notification if an FCM token is available.
7. The app queries the history and displays results, warnings, and bounding boxes when available.

### Frontend Architecture

![Frontend architecture diagram](images/architecture-frontend.png)

The frontend separates views, controllers, and services. Views render the interface and emit screen events, controllers coordinate state and navigation, and services encapsulate communication with Firebase, the backend API, notifications, and local preference storage.

### Backend Architecture

![Backend architecture diagram](images/architecture-backend.png)

The backend organizes the code into presentation, business, data, and infrastructure layers. The presentation layer exposes HTTP endpoints, the business layer executes analysis use cases, the data layer persists results, and the infrastructure layer integrates Firebase, PostgreSQL, Ollama, and the asynchronous queue.

## Local Deployment

Local deployment requires configuring the backend and frontend separately. Docker Compose is the recommended backend option because it starts PostgreSQL, Ollama, and the API with a consistent setup.

### Requirements

- Python 3.10 for running the backend manually.
- Docker and Docker Compose for running the backend, PostgreSQL, and Ollama in containers.
- Node.js 22 and npm for the frontend.
- Android Studio if you want to run the native app with `npm run android`.
- A Firebase project with Authentication enabled and a Firebase Admin service account.
- A Firebase `google-services.json` file for Android.

### Backend With Docker Compose

Create a `backend/.env` file with the variables used by `backend/docker-compose.yml`:

```env
POSTGRES_USER=climanuvem
POSTGRES_PASSWORD=climanuvem
POSTGRES_DB=climanuvem
OLLAMA_MODEL=gemma4:e4b
```

Variable reference:

- `POSTGRES_USER`: user that the PostgreSQL container creates when initializing the database.
- `POSTGRES_PASSWORD`: password for the PostgreSQL user.
- `POSTGRES_DB`: database name used by ClimaNuvem.
- `OLLAMA_MODEL`: model downloaded by the `ollama-pull` service and used by the backend to analyze images.

Download the private credentials JSON from Firebase Admin SDK and place it at:

```text
backend/secrets/firebase_key.json
```

This file must not be committed to the repository.

Start the services:

```bash
cd backend
docker compose up --build
```

Docker Compose starts:

- PostgreSQL 15.
- Ollama.
- A helper service that downloads the model configured in `OLLAMA_MODEL`.
- The FastAPI backend at `http://localhost:8000`.

### Manual Backend Setup

If you do not use Docker for the backend, PostgreSQL and Ollama must be running separately. Create a `backend/.env` file with:

```env
DATABASE_URL=postgresql://climanuvem:climanuvem@localhost:5432/climanuvem
FIREBASE_KEY_PATH=secrets/firebase_key.json
FIREBASE_CLOCK_SKEW_SECONDS=5
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=gemma4:e4b
CORS_ALLOW_ORIGINS=http://localhost:8081,http://localhost:19006,http://127.0.0.1:8081,http://127.0.0.1:19006
LOG_LEVEL=INFO
TEST_MODE=false
DISABLE_WORKER=false
```

Variable reference:

- `DATABASE_URL`: connection string used by SQLAlchemy to access PostgreSQL.
- `FIREBASE_KEY_PATH`: path to the private Firebase Admin credentials JSON, relative to the `backend/` directory.
- `FIREBASE_CLOCK_SKEW_SECONDS`: tolerance window, in seconds, for small clock skews when validating Firebase tokens.
- `OLLAMA_URL`: Ollama HTTP endpoint used by the backend to request analysis generation.
- `OLLAMA_MODEL`: specific model invoked by the Ollama client.
- `CORS_ALLOW_ORIGINS`: comma-separated list of origins allowed to call the backend during development.
- `LOG_LEVEL`: backend log verbosity, for example `DEBUG`, `INFO`, `WARNING`, or `ERROR`.
- `TEST_MODE`: when set to `true`, enables mocked authentication for tests; it should be `false` for normal development.
- `DISABLE_WORKER`: when set to `true`, prevents the asynchronous analysis worker from starting; it should be `false` for normal use.

Install dependencies and start the API:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup, the backend creates the required tables if they do not exist and initializes the cloud catalog when it is empty.

### Frontend

Create `frontend/.env` with the public variables that Expo injects into the app:

```env
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_TEST_MODE=false
EXPO_PUBLIC_DEFAULT_LANGUAGE=es
EXPO_PUBLIC_FIREBASE_API_KEY=...
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN=...
EXPO_PUBLIC_FIREBASE_PROJECT_ID=...
EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET=...
EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
EXPO_PUBLIC_FIREBASE_APP_ID=...
EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID=...
```

Variable reference:

- `EXPO_PUBLIC_BACKEND_URL`: base URL of the FastAPI backend called by the app.
- `EXPO_PUBLIC_TEST_MODE`: enables frontend test behavior when set to `true`.
- `EXPO_PUBLIC_DEFAULT_LANGUAGE`: preferred initial language; expected values are `es` or `en`.
- `EXPO_PUBLIC_FIREBASE_API_KEY`: public Firebase project key used by the client SDK.
- `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN`: authentication domain associated with the Firebase project.
- `EXPO_PUBLIC_FIREBASE_PROJECT_ID`: Firebase project identifier.
- `EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET`: storage bucket associated with the Firebase project.
- `EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`: sender identifier used by Firebase Cloud Messaging.
- `EXPO_PUBLIC_FIREBASE_APP_ID`: identifier of the app registered in Firebase.
- `EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID`: Firebase/Analytics measurement identifier, if configured.

Download `google-services.json` from the Android app settings in Firebase and place it at:

```text
frontend/google-services.json
```

This file must not be committed either.

Install dependencies and start Expo:

```bash
cd frontend
npm install
npm start
```

Common commands:

```bash
npm run android
npm run web
npm test
npm run lint
```

If you test on a physical phone, `EXPO_PUBLIC_BACKEND_URL` must not point to `localhost`, because `localhost` would refer to the phone itself. Use the local IP address of the machine running the backend, for example:

```env
EXPO_PUBLIC_BACKEND_URL=http://192.168.1.50:8000
```

For Android release builds, the app is configured with `usesCleartextTraffic=false`. Therefore, the published APK must communicate with an available HTTPS backend.

## APK Installation

The repository publishes signed APKs in GitHub Releases when the CI/CD workflow creates a release.

To install the app:

1. Open the releases page: [github.com/uo289165/epi-climanuvem/releases](https://github.com/uo289165/epi-climanuvem/releases).
2. In the latest release, download the `climanuvem-<run_number>.apk` asset.
3. Open the APK from the Android device.
4. If Android asks for permission, allow installation from unknown sources for the app used to open the file.
5. Install and open ClimaNuvem.

The APK uses the backend URL defined in `EXPO_PUBLIC_BACKEND_URL` during the CI build. For the app to work outside the local environment, that URL must point to an HTTPS backend reachable from the device.

## Tests And Quality

Backend:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Frontend:

```bash
cd frontend
npm test
npm run test:coverage
npm run lint
```

End-to-end system tests are maintained in a separate repository:

- **E2E test suite (RETORCH)**: [https://github.com/augustocristian/retorch-st-climanuvem](https://github.com/augustocristian/retorch-st-climanuvem)

SonarCloud reads coverage from:

- `backend/coverage.xml`, generated by `pytest`.
- `frontend/coverage/lcov.info`, generated by `npm run test:coverage`.

The following files are excluded from coverage calculations because they contain static data, generated/migration code, visual UI wrappers, or thin adapters around native/Firebase APIs that are validated through higher-level tests:

- `**/locales/**`
- `backend/app/infrastructure/database/seed_clouds.sql`
- `backend/app/infrastructure/database/migrations/**`
- `frontend/app/**`
- `frontend/components/**`
- `frontend/src/views/**`
- `frontend/src/styles/**`
- `frontend/src/config/**`
- `frontend/src/controllers/**`
- `frontend/src/hooks/**`
- `frontend/src/i18n.ts`
- `frontend/src/services/AuthService.ts`
- `frontend/src/services/LoggerService.ts`
- `frontend/src/services/NotificationService.ts`
- `frontend/src/services/mockData.ts`
- `frontend/src/utils/captureUtils.ts`
- `frontend/src/models/**`

The badges at the top of this README show the GitHub Actions workflow status and the SonarCloud Quality Gate.

## CI/CD

The `.github/workflows/ci-cd.yml` workflow runs checks by changed path:

- Changes in `backend/`: install Python dependencies and run `pytest`.
- Changes in `frontend/`: install Node dependencies, run `npm run lint`, and run `npm test`.
- Changes in `backend/` or `frontend/`: generate backend and frontend coverage reports and send the analysis to SonarCloud.
- Changes in `frontend/` on `main`: if tests pass, build a signed Android release APK and attach it to a new GitHub Release.
- Manual execution: the workflow can build Android manually through `workflow_dispatch` with `build_android=true`.

SonarCloud requires a GitHub Actions secret named `SONAR_TOKEN`. Without this secret, the SonarCloud analysis job fails even if the backend and frontend tests pass.

To configure it:

1. In SonarCloud, open `My Account > Security` and generate a token.
2. In GitHub, open the repository settings.
3. Go to `Settings > Secrets and variables > Actions > New repository secret`.
4. Create a secret named `SONAR_TOKEN`.
5. Paste the SonarCloud token as the secret value.

Secrets required to build the APK in GitHub Actions:

```text
ANDROID_KEYSTORE_BASE64
ANDROID_KEYSTORE_PASSWORD
ANDROID_KEY_ALIAS
ANDROID_KEY_PASSWORD
GOOGLE_SERVICES_JSON_BASE64
EXPO_PUBLIC_BACKEND_URL
EXPO_PUBLIC_FIREBASE_API_KEY
EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN
EXPO_PUBLIC_FIREBASE_PROJECT_ID
EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET
EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
EXPO_PUBLIC_FIREBASE_APP_ID
EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID
```

Secret reference:

- `ANDROID_KEYSTORE_BASE64`: Android keystore encoded in Base64 for signing the APK.
- `ANDROID_KEYSTORE_PASSWORD`: keystore password.
- `ANDROID_KEY_ALIAS`: alias of the signing key inside the keystore.
- `ANDROID_KEY_PASSWORD`: signing key password.
- `GOOGLE_SERVICES_JSON_BASE64`: contents of `google-services.json` encoded in Base64.
- `EXPO_PUBLIC_BACKEND_URL`: HTTPS backend URL embedded into the APK.
- `EXPO_PUBLIC_FIREBASE_API_KEY`: public Firebase project key for the client SDK.
- `EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN`: Firebase authentication domain.
- `EXPO_PUBLIC_FIREBASE_PROJECT_ID`: Firebase project identifier.
- `EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET`: Firebase project storage bucket.
- `EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`: Firebase Cloud Messaging sender identifier.
- `EXPO_PUBLIC_FIREBASE_APP_ID`: identifier of the app registered in Firebase.
- `EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID`: Firebase/Analytics measurement identifier.

## Contributing

To contribute to the project:

- Open an issue or create a branch with a descriptive name before starting a relevant change.
- Keep changes focused and document in the pull request which problem they solve.
- Run the checks that apply to the modified area: `pytest` for backend, `npm test` and `npm run lint` for frontend.
- Do not commit credentials, `.env` files, Firebase keys, Android keystores, or private local files.
- Update the documentation when commands, environment variables, architecture, or user-visible flows change.
- Explain in the pull request how the change was verified, and attach screenshots when the UI is affected.

## How To Cite

If you use this software, please cite the project as:

Uria Navarro, F., Augusto, C., Gallego Becerra, M. Á., & Pérez Vellarino, T. (2026). ClimaNuvem (Version 1.0.0) [Computer software]. https://github.com/uo289165/epi-climanuvem

You can also check the formal citation metadata in `CITATION.cff`.
