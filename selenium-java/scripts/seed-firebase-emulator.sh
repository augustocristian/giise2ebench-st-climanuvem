#!/usr/bin/env bash
# Creates the Selenium test accounts in the Firebase Auth emulator and writes accounts.local.csv.
set -euo pipefail

EMULATOR_URL="${FIREBASE_EMULATOR_URL:-http://localhost:9099}"
API_KEY="${FIREBASE_API_KEY:-demo-api-key}"
PROJECT_ID="${FIREBASE_PROJECT_ID:-demo-climanuvem}"
PASSWORD="${TEST_ACCOUNT_PASSWORD:-Test-pass-123}"
OUT="${ACCOUNTS_FILE:-$(dirname "$0")/../src/test/resources/accounts.local.csv}"
AUTH_API="$EMULATOR_URL/identitytoolkit.googleapis.com/v1"

create_verified_user() {
  local email="$1" response local_id
  response=$(curl -sf -X POST "$AUTH_API/accounts:signUp?key=$API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$email\",\"password\":\"$PASSWORD\",\"returnSecureToken\":true}")
  local_id=$(echo "$response" | sed -n 's/.*"localId": *"\([^"]*\)".*/\1/p')
  # Only the emulator's admin endpoint ("Bearer owner") may set emailVerified.
  curl -sf -X POST "$AUTH_API/projects/$PROJECT_ID/accounts:update" \
    -H 'Content-Type: application/json' -H 'Authorization: Bearer owner' \
    -d "{\"localId\":\"$local_id\",\"emailVerified\":true}" >/dev/null
}

create_verified_user "login_user@example.test"
create_verified_user "profile_user@example.test"

cat > "$OUT" <<CSV
role,email,password,verified,description
login_user,login_user@example.test,$PASSWORD,true,Existing account for login tests
profile_user,profile_user@example.test,$PASSWORD,true,Verified account for profile tests
unknown_user,missing@example.test,wrong-password,false,Non-existing account for negative login tests
CSV
echo "Seeded emulator accounts and wrote $OUT"
