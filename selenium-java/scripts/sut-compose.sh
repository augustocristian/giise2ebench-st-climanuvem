#!/usr/bin/env bash
# docker compose for the system-test stack: prod compose + dev override (Firebase emulator) + test override.
# Usage: scripts/sut-compose.sh up -d --build db firebase-emulator backend frontend
# Set WITH_OLLAMA=true to also include the real analysis worker.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FILES=(
  -f "$ROOT/sut/backend/docker-compose.yml"
  -f "$ROOT/sut/backend/docker-compose.dev.override.yml"
  -f "$ROOT/selenium-java/docker-compose.test.override.yml"
)
if [ "${WITH_OLLAMA:-false}" = "true" ]; then
  FILES+=(-f "$ROOT/selenium-java/docker-compose.ollama-test.yml")
fi

exec docker compose --project-name climanuvem-test --env-file "$ROOT/selenium-java/test.env" "${FILES[@]}" "$@"
