#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "python not found; cannot run SAST/dependency scan" >&2
  exit 1
fi

python -m pip install --quiet --upgrade pip
python -m pip install --quiet pip-audit safety bandit

echo "Running pip-audit..."
pip-audit -r "$ROOT_DIR/requirements.txt"

echo "Running bandit on backend and core..."
bandit -q -r "$ROOT_DIR/backend" "$ROOT_DIR/core"

if command -v npm >/dev/null 2>&1 && [ -f "$ROOT_DIR/frontend/package-lock.json" ]; then
  echo "Running npm audit (high severity) ..."
  (cd "$ROOT_DIR/frontend" && npm audit --audit-level=high --production)
else
  echo "Skipping npm audit; npm or package-lock.json not available"
fi
