#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

API_PORT="${API_HOST_PORT:-18000}"
UI_PORT="${UI_HOST_PORT:-4173}"
POSTGRES_PORT="${POSTGRES_HOST_PORT:-15432}"
REDIS_PORT="${REDIS_HOST_PORT:-16379}"
OLLAMA_PORT="${OLLAMA_HOST_PORT:-21434}"
SEED_DEV_DATA="${SEED_DEV_DATA:-false}"
WAIT_SECONDS="${WAIT_SECONDS:-90}"

log() {
  printf '\n[%s] %s\n' "xyntra-start" "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local deadline=$((SECONDS + WAIT_SECONDS))

  until curl --silent --fail "${url}" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      echo "Timed out waiting for ${label} at ${url}" >&2
      exit 1
    fi
    sleep 2
  done
}

require_cmd docker
require_cmd curl

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required." >&2
  exit 1
fi

log "Ensuring environment file exists"
cp -n .env.example .env || true

log "Building API and worker images"
docker compose build api worker >/dev/null

log "Starting infrastructure services"
docker compose up -d postgres redis ollama

log "Waiting for PostgreSQL and Redis health"
docker compose up -d postgres redis >/dev/null

log "Ensuring database extension and test database"
docker compose exec -T postgres psql -U xyntra -d xyntra -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null
docker compose exec -T postgres psql -U xyntra -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'xyntra_test';" | grep -q 1 \
  || docker compose exec -T postgres psql -U xyntra -d postgres -c "CREATE DATABASE xyntra_test;" >/dev/null
docker compose exec -T postgres psql -U xyntra -d xyntra_test -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null

log "Applying database migrations"
docker compose run --no-deps --rm api alembic upgrade head >/dev/null

log "Starting application services"
docker compose up -d api worker ui

log "Waiting for API readiness"
wait_for_http "http://localhost:${API_PORT}/api/v1/ready" "API"

log "Waiting for UI"
wait_for_http "http://localhost:${UI_PORT}" "UI"

if [[ "${SEED_DEV_DATA}" == "true" ]]; then
  log "Seeding development data"
  BASE_URL="http://localhost:${API_PORT}/api/v1" ./scripts/seed_dev_data.sh
fi

cat <<EOF

Xyntra is ready.

API:      http://localhost:${API_PORT}
UI:       http://localhost:${UI_PORT}
Postgres: localhost:${POSTGRES_PORT}
Redis:    localhost:${REDIS_PORT}
Ollama:   localhost:${OLLAMA_PORT}

Optional seed:
  SEED_DEV_DATA=true ./scripts/start_xyntra.sh

Stop the stack:
  docker compose down
EOF
