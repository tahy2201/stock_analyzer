#!/bin/sh
set -e

echo "Initializing database schema..."
if ! python -m shared.database.models; then
    echo "Failed to initialize database schema" >&2
    exit 1
fi

echo "Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
