#!/bin/sh
set -e

UVICORN_ARGS="${UVICORN_EXTRA_ARGS:-}"

if [ "${UVICORN_RELOAD:-0}" = "1" ]; then
    UVICORN_ARGS="--reload ${UVICORN_ARGS}"
fi

echo "Running database migrations..."
if ! python -m alembic upgrade head; then
    echo "Failed to run database migrations" >&2
    exit 1
fi

echo "Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000 ${UVICORN_ARGS}
