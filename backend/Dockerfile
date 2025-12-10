FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies required for scientific Python packages and uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip uv

# Copy only dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock* ./

# Install backend dependencies using uv (as per project rules)
RUN uv pip install --system .

# Then copy the rest of the application
COPY . .

# Ensure the data directory exists for the SQLite database
RUN mkdir -p /app/data

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
