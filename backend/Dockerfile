FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies required for scientific Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the project metadata first to leverage Docker layer caching
COPY pyproject.toml uv.lock* ./ 2>/dev/null || true
COPY . .

# Install backend dependencies
RUN pip install --upgrade pip \
    && pip install .

# Ensure the data directory exists for the SQLite database
RUN mkdir -p /app/data

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
