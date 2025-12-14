#!/bin/sh
set -e

echo "Running database migrations..."
if ! python -m alembic upgrade head; then
    echo "Failed to run database migrations" >&2
    exit 1
fi

echo "Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
