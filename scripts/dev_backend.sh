#!/usr/bin/env bash
# Convenience script: set up venv, install, seed, and run the backend.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -e ./analytics
pip install -r backend/requirements.txt

[ -f .env ] || cp .env.example .env
python -m backend.app.seed
echo "Starting RiskLens API on http://localhost:8000 (docs at /docs)"
uvicorn backend.app.main:app --reload --port 8000
