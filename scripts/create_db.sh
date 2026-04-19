#!/usr/bin/env bash
set -euo pipefail

docker compose up -d postgres
docker compose exec postgres psql -U xyntra -d xyntra -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec -T postgres psql -U xyntra -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'xyntra_test';" | grep -q 1 \
  || docker compose exec -T postgres psql -U xyntra -d postgres -c "CREATE DATABASE xyntra_test;"
docker compose exec postgres psql -U xyntra -d xyntra_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "Database extension setup completed."
