#!/bin/bash
# ラズパイに環境変数ファイルを作成するスクリプト

set -e

echo "🔧 Setting up production environment variables on Raspberry Pi..."

# 環境変数チェック
if [ -z "$PROD_RASPI_IP" ]; then
    read -p "Enter Raspberry Pi IP address: " PROD_RASPI_IP
fi

if [ -z "$PROD_BACKEND_URL" ]; then
    PROD_BACKEND_URL="http://${PROD_RASPI_IP}:8000"
fi

if [ -z "$PROD_FRONTEND_URL" ]; then
    PROD_FRONTEND_URL="http://${PROD_RASPI_IP}:4173"
fi

# ラズパイに接続してプロジェクトディレクトリを作成
RASPI_USER="${PROD_RASPI_USER:-pi}"
RASPI_PROJECT_DIR="${PROD_RASPI_PROJECT_DIR:-/home/${RASPI_USER}/stock_analyzer}"

echo "📝 Creating .env file on Raspberry Pi..."

ssh "${RASPI_USER}@${PROD_RASPI_IP}" << EOF
mkdir -p ${RASPI_PROJECT_DIR}
cd ${RASPI_PROJECT_DIR}

cat > .env << 'ENVFILE'
# Production environment variables
PROD_API_BASE_URL=${PROD_BACKEND_URL}/api
PROD_FRONTEND_URL=${PROD_FRONTEND_URL}
PROD_BACKEND_URL=${PROD_BACKEND_URL}
ENVFILE

echo "✅ Environment file created at ${RASPI_PROJECT_DIR}/.env"
cat .env
EOF

echo ""
echo "✅ Environment setup completed!"
echo ""
echo "📊 Environment variables:"
echo "   PROD_API_BASE_URL=${PROD_BACKEND_URL}/api"
echo "   PROD_FRONTEND_URL=${PROD_FRONTEND_URL}"
echo "   PROD_BACKEND_URL=${PROD_BACKEND_URL}"
