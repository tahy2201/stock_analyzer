#!/bin/bash
# 本番環境（ラズパイ）のDBを開発環境に同期するスクリプト

set -e

echo "📥 Syncing database from production (Raspberry Pi)..."

# 環境変数チェック
RASPI_USER="${PROD_RASPI_USER:-pi}"
RASPI_IP="${PROD_RASPI_IP}"
RASPI_PROJECT_DIR="${PROD_RASPI_PROJECT_DIR:-/home/${RASPI_USER}/stock_analyzer}"

if [ -z "$RASPI_IP" ]; then
    read -p "Enter Raspberry Pi IP address: " RASPI_IP
fi

# ローカルのdataディレクトリを作成
mkdir -p ./data

# 既存のDBがある場合はバックアップ
LOCAL_DB="./data/stock_data.db"
if [ -f "$LOCAL_DB" ]; then
    BACKUP_FILE="./data/stock_data.db.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up existing database to $BACKUP_FILE"
    cp "$LOCAL_DB" "$BACKUP_FILE"
fi

# 本番環境のDBファイルの存在確認
echo "🔍 Checking database on Raspberry Pi..."
REMOTE_DB_EXISTS=$(ssh "${RASPI_USER}@${RASPI_IP}" "[ -f ${RASPI_PROJECT_DIR}/data/stock_data.db ] && echo 'yes' || echo 'no'")

if [ "$REMOTE_DB_EXISTS" != "yes" ]; then
    echo "❌ Error: Database file not found on Raspberry Pi"
    echo "   Expected location: ${RASPI_PROJECT_DIR}/data/stock_data.db"
    exit 1
fi

# DBのサイズ確認
REMOTE_DB_SIZE=$(ssh "${RASPI_USER}@${RASPI_IP}" "du -h ${RASPI_PROJECT_DIR}/data/stock_data.db | cut -f1")
echo "📊 Remote database size: $REMOTE_DB_SIZE"

# DBファイルを取得
echo "📥 Downloading database from Raspberry Pi..."
scp "${RASPI_USER}@${RASPI_IP}:${RASPI_PROJECT_DIR}/data/stock_data.db" "$LOCAL_DB"

# 同期後のサイズ確認
LOCAL_DB_SIZE=$(du -h "$LOCAL_DB" | cut -f1)

echo "✅ Database sync completed!"
echo ""
echo "📊 Summary:"
echo "   Source: ${RASPI_USER}@${RASPI_IP}:${RASPI_PROJECT_DIR}/data/stock_data.db ($REMOTE_DB_SIZE)"
echo "   Destination: $LOCAL_DB ($LOCAL_DB_SIZE)"
echo ""
echo "💡 Tip: To verify the data, run:"
echo "   sqlite3 $LOCAL_DB 'SELECT COUNT(*) FROM companies;'"
