#!/bin/bash
# 本番環境（ラズパイ）のDBを開発環境に同期するスクリプト

set -e

# パス設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
LOCAL_DB="$DATA_DIR/stock_data.db"

# 環境変数を読み込み（.envファイルがあれば）
[ -f "$SCRIPT_DIR/.env" ] && source "$SCRIPT_DIR/.env"

# ラズパイ接続設定
RASPI_USER="${PROD_RASPI_USER:-pi}"
RASPI_IP="${PROD_RASPI_IP}"
RASPI_PROJECT_DIR="${PROD_RASPI_PROJECT_DIR:-/home/${RASPI_USER}/stock_analyzer}"
REMOTE_DB="${RASPI_PROJECT_DIR}/data/stock_data.db"

# IPアドレスが未設定の場合は入力を求める
if [ -z "$RASPI_IP" ]; then
    read -p "Enter Raspberry Pi IP address: " RASPI_IP
fi

echo "📥 Syncing database from production (Raspberry Pi)..."

# ローカルのdataディレクトリを作成
mkdir -p "$DATA_DIR"

# 既存のDBがある場合はバックアップ
if [ -f "$LOCAL_DB" ]; then
    BACKUP_FILE="${LOCAL_DB}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up existing database to $BACKUP_FILE"
    cp "$LOCAL_DB" "$BACKUP_FILE"
fi

# 本番環境のDBファイルの存在確認とサイズ取得
echo "🔍 Checking database on Raspberry Pi..."
REMOTE_HOST="${RASPI_USER}@${RASPI_IP}"

if ! ssh "$REMOTE_HOST" "[ -f $REMOTE_DB ]"; then
    echo "❌ Error: Database file not found on Raspberry Pi"
    echo "   Expected location: $REMOTE_DB"
    exit 1
fi

REMOTE_DB_SIZE=$(ssh "$REMOTE_HOST" "du -h $REMOTE_DB | cut -f1")
echo "📊 Remote database size: $REMOTE_DB_SIZE"

# DBファイルを取得
echo "📥 Downloading database..."
scp "${REMOTE_HOST}:${REMOTE_DB}" "$LOCAL_DB"

# 同期完了
LOCAL_DB_SIZE=$(du -h "$LOCAL_DB" | cut -f1)

echo "✅ Database sync completed!"
echo ""
echo "📊 Summary:"
echo "   Source: ${REMOTE_HOST}:${REMOTE_DB} ($REMOTE_DB_SIZE)"
echo "   Destination: $LOCAL_DB ($LOCAL_DB_SIZE)"
echo ""
echo "💡 Tip: sqlite3 $LOCAL_DB 'SELECT COUNT(*) FROM companies;'"
