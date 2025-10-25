#!/bin/sh
set -e

# Ensure database schema exists before starting the API
python -m shared.database.models >/dev/null 2>&1 || true

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
