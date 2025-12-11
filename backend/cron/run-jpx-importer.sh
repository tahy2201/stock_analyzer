#!/bin/bash
# JPX企業リストインポートバッチを実行するスクリプト
# cron用

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$HOME/logs/jpx-importer.log"

# ログディレクトリを作成
mkdir -p "$(dirname "$LOG_FILE")"

# タイムスタンプ付きログ
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting JPX importer..." >> "$LOG_FILE"

# Dockerコンテナ内でバッチを実行
cd "$PROJECT_DIR"
docker compose -f docker-compose.prod.yml exec -T backend python -m batch.jpx_importer >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] JPX importer completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] JPX importer failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
