#!/bin/bash
# 開発環境のDBを本番環境（ラズパイ）に移行するスクリプト

set -e

echo "📦 Migrating database to production (Raspberry Pi)..."

# 環境変数チェック
RASPI_USER="${PROD_RASPI_USER:-pi}"
RASPI_IP="${PROD_RASPI_IP}"
RASPI_PROJECT_DIR="${PROD_RASPI_PROJECT_DIR:-/home/${RASPI_USER}/stock_analyzer}"

if [ -z "$RASPI_IP" ]; then
    read -p "Enter Raspberry Pi IP address: " RASPI_IP
fi

# DBファイルの存在確認
LOCAL_DB="./data/stock_data.db"
if [ ! -f "$LOCAL_DB" ]; then
    echo "❌ Error: Database file not found at $LOCAL_DB"
    exit 1
fi

# DBのサイズ確認
DB_SIZE=$(du -h "$LOCAL_DB" | cut -f1)
echo "📊 Database size: $DB_SIZE"

# 本番環境にdataディレクトリを作成
echo "📁 Creating data directory on Raspberry Pi..."
ssh "${RASPI_USER}@${RASPI_IP}" "mkdir -p ${RASPI_PROJECT_DIR}/data"

# 既存のDBがある場合はバックアップ
echo "💾 Checking for existing database..."
ssh "${RASPI_USER}@${RASPI_IP}" << EOF
if [ -f "${RASPI_PROJECT_DIR}/data/stock_data.db" ]; then
    BACKUP_FILE="${RASPI_PROJECT_DIR}/data/stock_data.db.backup.\$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing database to \$BACKUP_FILE"
    cp "${RASPI_PROJECT_DIR}/data/stock_data.db" "\$BACKUP_FILE"
fi
EOF

# DBファイルを転送
echo "🚀 Transferring database to Raspberry Pi..."
scp "$LOCAL_DB" "${RASPI_USER}@${RASPI_IP}:${RASPI_PROJECT_DIR}/data/"

echo "✅ Database migration completed!"
echo ""
echo "📊 Summary:"
echo "   Source: $LOCAL_DB ($DB_SIZE)"
echo "   Destination: ${RASPI_USER}@${RASPI_IP}:${RASPI_PROJECT_DIR}/data/stock_data.db"
