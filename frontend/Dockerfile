FROM oven/bun:1 AS base

WORKDIR /app

# ビルド時にAPIエンドポイントを指定（docker-composeから渡される）
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# 依存を一度だけ入れて各ステージで共有
COPY bun.lock package.json ./
RUN bun install --frozen-lockfile

# ---------- 開発（ホットリロード） ----------
FROM base AS dev
COPY . .
EXPOSE 4173
CMD ["bun", "run", "dev", "--host", "0.0.0.0", "--port", "4173"]

# ---------- 本番ビルド ----------
FROM base AS build
COPY . .
RUN bun run build

FROM oven/bun:1 AS prod
WORKDIR /app

# ビルド成果物と preview に必要な最低限のファイルだけをコピー
COPY --from=build /app/dist ./dist
COPY --from=build /app/vite.config.ts ./
COPY --from=base /app/package.json /app/bun.lock ./
RUN bun install --frozen-lockfile

EXPOSE 4173

CMD ["bun", "run", "preview", "--host", "0.0.0.0", "--port", "4173"]
