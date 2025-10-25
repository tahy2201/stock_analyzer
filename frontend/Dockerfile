FROM oven/bun:1 AS base

WORKDIR /app

# Configure build-time API endpoint (can be overridden via build args)
ARG VITE_API_BASE_URL="http://localhost:8000/api"
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Install dependencies using the lockfile for reproducibility
COPY bun.lock package.json .
RUN bun install --frozen-lockfile

# Copy the rest of the frontend source code and build the production bundle
COPY . .
RUN bun run build

EXPOSE 4173

CMD ["bun", "run", "preview", "--host", "0.0.0.0", "--port", "4173"]
