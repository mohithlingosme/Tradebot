#!/bin/bash

# Market Data Ingestion API - cURL Examples
# Replace localhost:8001 with your actual API endpoint

BASE_URL="http://localhost:8001"

echo "=== Market Data Ingestion API Examples ==="
echo

# Health Check
echo "1. Health Check:"
curl -s "${BASE_URL}/health" | jq .
echo -e "\n"

# Readiness Check
echo "2. Readiness Check:"
curl -s "${BASE_URL}/ready" | jq .
echo -e "\n"

# Get Candles for RELIANCE.NS
echo "3. Get Candles for RELIANCE.NS (1m interval, limit 10):"
curl -s "${BASE_URL}/candles?symbol=RELIANCE.NS&interval=1m&limit=10" | jq .
echo -e "\n"

# Get Candles for AAPL
echo "4. Get Candles for AAPL (1d interval, limit 5):"
curl -s "${BASE_URL}/candles?symbol=AAPL&interval=1d&limit=5" | jq .
echo -e "\n"

# Get Available Symbols
echo "5. Get Available Symbols:"
curl -s "${BASE_URL}/symbols" | jq .
echo -e "\n"

# Get Prometheus Metrics
echo "6. Get Prometheus Metrics:"
curl -s "${BASE_URL}/metrics" | head -20
echo "... (truncated)"
echo

echo "=== CLI Commands Examples ==="
echo

# Migrate Database
echo "7. Run Database Migration:"
echo "python -m src.cli migrate"
echo

# Backfill Historical Data
echo "8. Backfill Historical Data:"
echo "python -m src.cli backfill --symbols RELIANCE.NS TCS.NS --period 7d --interval 1d"
echo

# Start Realtime Ingestion
echo "9. Start Realtime Ingestion:"
echo "python -m src.cli realtime --symbols RELIANCE.NS TCS.NS --provider mock"
echo

# Start Mock WebSocket Server
echo "10. Start Mock WebSocket Server:"
echo "python -m src.cli mock-server"
echo

echo "=== Docker Compose Examples ==="
echo

# Start Development Environment
echo "11. Start Development Environment:"
echo "docker-compose up -d"
echo

# Start Staging Environment
echo "12. Start Staging Environment:"
echo "docker-compose --profile staging up -d"
echo

# Start Sandbox Environment
echo "13. Start Sandbox Environment:"
echo "docker-compose --profile sandbox up -d"
echo

echo "=== Testing Examples ==="
echo

# Run Unit Tests
echo "14. Run Unit Tests:"
echo "pytest tests/unit/ -v"
echo

# Run Integration Tests
echo "15. Run Integration Tests:"
echo "pytest tests/integration/ -v"
echo

# Run All Tests with Coverage
echo "16. Run All Tests with Coverage:"
echo "pytest --cov=market_data_ingestion --cov-report=html"
echo

echo "=== Sample Data Import ==="
echo

# Import Sample CSV Data
echo "17. Import Sample CSV Data:"
echo "python -m src.cli backfill --csv-file examples/sample_minute.csv"
echo
