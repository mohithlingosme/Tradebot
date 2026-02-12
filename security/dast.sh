#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "DAST smoke against ${BASE_URL}"

if ! curl --output /dev/null --silent --head --fail "${BASE_URL}/health"; then
  echo "Backend not running at ${BASE_URL}; skipping DAST probes."
  exit 0
fi

status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
if [[ "$status" -ne 200 ]]; then
  echo "/health returned ${status}, expected 200" >&2
  exit 1
fi

unauth_status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/auth/me")
if [[ "$unauth_status" -lt 400 ]]; then
  echo "Unauthenticated access to /auth/me returned ${unauth_status}, expected auth failure" >&2
  exit 1
fi

echo "DAST smoke checks passed"
