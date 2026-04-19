#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
USER_ID="${USER_ID:-11111111-1111-1111-1111-111111111111}"

echo "Seeding development data against ${BASE_URL}"

PROJECT_RESPONSE="$(curl --fail --silent --show-error \
  -X POST "${BASE_URL}/projects" \
  -H "Content-Type: application/json" \
  -d "{
    \"owner_id\": \"${USER_ID}\",
    \"name\": \"Xyntra Dev Project\",
    \"description\": \"Seeded development project\",
    \"local_only\": false,
    \"token_quota\": 50000
  }")"

PROJECT_ID="$(PROJECT_RESPONSE="${PROJECT_RESPONSE}" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["PROJECT_RESPONSE"])
print(payload["id"])
PY
)"

SESSION_RESPONSE="$(curl --fail --silent --show-error \
  -X POST "${BASE_URL}/projects/${PROJECT_ID}/sessions" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"title\": \"Seeded Session\"
  }")"

SESSION_ID="$(SESSION_RESPONSE="${SESSION_RESPONSE}" python3 - <<'PY'
import json
import os

payload = json.loads(os.environ["SESSION_RESPONSE"])
print(payload["id"])
PY
)"

curl --fail --silent --show-error \
  -X PUT "${BASE_URL}/projects/${PROJECT_ID}/state" \
  -H "Content-Type: application/json" \
  -d '{
    "state": {
      "branch": "main",
      "summary": "Seeded local development state"
    }
  }' >/dev/null

curl --fail --silent --show-error \
  -X POST "${BASE_URL}/projects/${PROJECT_ID}/sessions/${SESSION_ID}/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "Seeded hello from local development",
    "attachments": []
  }' >/dev/null

curl --fail --silent --show-error \
  -X POST "${BASE_URL}/tasks" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"${PROJECT_ID}\",
    \"session_id\": \"${SESSION_ID}\",
    \"name\": \"seeded-task\",
    \"task_type\": \"bootstrap\",
    \"input_payload\": {
      \"objective\": \"validate seeded workflow\"
    },
    \"description\": \"Seeded task for local smoke testing\"
  }" >/dev/null

echo "Seed data created for project ${PROJECT_ID} and session ${SESSION_ID}."
