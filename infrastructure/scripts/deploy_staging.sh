#!/usr/bin/env bash
set -euo pipefail

COMPOSE="docker compose -f infrastructure/docker-compose.yml --profile staging"

echo "Pulling latest staging images..."
$COMPOSE pull backend_api market_data_ingestion_staging || true

echo "Starting staging services..."
$COMPOSE up -d --build backend_api market_data_ingestion_staging

echo "Staging deployment finished."
