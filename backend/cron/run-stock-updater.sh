#!/bin/bash
# 株価データ更新バッチを実行するスクリプト
# cron用

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"  # backend/cron -> backend -> stock_analyzer
LOG_FILE="$HOME/logs/stock-updater.log"

# ログディレクトリを作成
mkdir -p "$(dirname "$LOG_FILE")"

# タイムスタンプ付きログ
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting stock updater..." >> "$LOG_FILE"

# Dockerコンテナ内でバッチを実行
cd "$PROJECT_DIR"
docker compose -f docker-compose.prod.yml exec -T backend python -m batch.stock_updater >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stock updater completed successfully" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stock updater failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
