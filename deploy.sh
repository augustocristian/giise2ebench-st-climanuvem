#!/usr/bin/env bash
# Convenience wrapper to deploy the ClimaNuvem SUT (sut/backend + sut/frontend) locally.
#
# Usage:
#   ./deploy.sh backend    # docker compose up --build for Postgres + Ollama + FastAPI API
#   ./deploy.sh frontend   # npm install && start the Expo dev server
#   ./deploy.sh all        # backend (detached) + frontend (foreground)
#   ./deploy.sh down       # docker compose down for the backend (add --volumes to wipe DB/Ollama data)
#
# Prerequisites (see sut/README.md for full detail):
#   - Docker + Docker Compose for the backend
#   - Node.js 22 + npm for the frontend
#   - sut/backend/.env with POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, OLLAMA_MODEL
#   - sut/backend/secrets/firebase_key.json (Firebase Admin credentials)
#   - sut/frontend/.env with EXPO_PUBLIC_* variables

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/sut/backend"
FRONTEND_DIR="$ROOT_DIR/sut/frontend"

usage() {
  echo "Usage: $0 {backend|frontend|all|down} [--detach|--volumes]"
  exit 1
}

deploy_backend() {
  local detach_flag="${1:-}"

  if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "ERROR: $BACKEND_DIR/.env not found." >&2
    echo "Create it with POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, OLLAMA_MODEL (see sut/README.md)." >&2
    exit 1
  fi

  if [ ! -f "$BACKEND_DIR/secrets/firebase_key.json" ]; then
    echo "WARNING: $BACKEND_DIR/secrets/firebase_key.json not found." >&2
    echo "Firebase-authenticated requests will fail until it is provided." >&2
  fi

  echo "==> Starting backend (PostgreSQL, Ollama, FastAPI) via Docker Compose"
  (
    cd "$BACKEND_DIR"
    if [ "$detach_flag" = "--detach" ]; then
      docker compose up --build -d
    else
      docker compose up --build
    fi
  )
}

stop_backend() {
  local volumes_flag="${1:-}"

  echo "==> Stopping backend (Docker Compose)"
  (
    cd "$BACKEND_DIR"
    if [ "$volumes_flag" = "--volumes" ]; then
      echo "==> Also removing volumes (Postgres data + Ollama models will be deleted)"
      docker compose down --volumes
    else
      docker compose down
    fi
  )
}

deploy_frontend() {
  if [ ! -f "$FRONTEND_DIR/.env" ]; then
    echo "WARNING: $FRONTEND_DIR/.env not found." >&2
    echo "Create it with EXPO_PUBLIC_BACKEND_URL and EXPO_PUBLIC_FIREBASE_* variables (see sut/README.md)." >&2
  fi

  echo "==> Installing frontend dependencies"
  (cd "$FRONTEND_DIR" && npm install)

  echo "==> Starting Expo dev server"
  (cd "$FRONTEND_DIR" && npm start)
}

[ $# -ge 1 ] || usage

case "$1" in
  backend)
    deploy_backend "${2:-}"
    ;;
  frontend)
    deploy_frontend
    ;;
  all)
    deploy_backend --detach
    echo "==> Backend started in the background. Tail logs with: (cd sut/backend && docker compose logs -f)"
    deploy_frontend
    ;;
  down)
    stop_backend "${2:-}"
    ;;
  *)
    usage
    ;;
esac
