#!/bin/bash
# 本番環境デプロイスクリプト
# Raspberry Pi上で実行してください

set -e

echo "📦 Stock Analyzer デプロイスクリプト"
echo ""

# カレントディレクトリの確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 引数からタグ名を取得（オプション）
TAG_NAME="$1"

if [ -z "$TAG_NAME" ]; then
    echo "❓ デプロイするバージョンを指定してください"
    echo ""
    echo "利用可能なタグ一覧:"
    git fetch --tags 2>/dev/null || true
    git tag -l | tail -10
    echo ""
    read -p "デプロイするタグ名を入力 (例: v1.0.0): " TAG_NAME

    if [ -z "$TAG_NAME" ]; then
        echo "❌ タグ名が入力されませんでした"
        exit 1
    fi
fi

echo "🔍 タグを確認中: $TAG_NAME"

# リモートからタグを取得
echo "📥 最新のタグを取得中..."
git fetch --tags

# タグが存在するか確認
if ! git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    echo "❌ エラー: タグ '$TAG_NAME' が見つかりません"
    echo ""
    echo "利用可能なタグ一覧:"
    git tag -l | tail -10
    exit 1
fi

# 現在のブランチ/タグを確認
CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
echo "📍 現在のバージョン: $CURRENT_VERSION"
echo "📍 デプロイ先バージョン: $TAG_NAME"
echo ""

# 確認プロンプト
read -p "このバージョンをデプロイしますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ デプロイをキャンセルしました"
    exit 0
fi

echo ""
echo "🚀 デプロイを開始します..."
echo ""

# タグにチェックアウト
echo "📝 タグ $TAG_NAME にチェックアウト中..."
git checkout "$TAG_NAME"

# 既存のコンテナを停止
echo "🛑 既存のコンテナを停止中..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# コンテナをビルドして起動
echo "🔨 コンテナをビルド中..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "🚀 コンテナを起動中..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 起動確認
echo ""
echo "⏳ コンテナの起動を待機中..."
sleep 5

# コンテナの状態を確認
echo ""
echo "📊 コンテナの状態:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo ""
echo "✅ デプロイが完了しました！"
echo ""
echo "📍 デプロイされたバージョン: $TAG_NAME"
echo ""
echo "🌐 アクセスURL:"
echo "   フロントエンド: http://$(hostname -I | awk '{print $1}'):4173"
echo "   バックエンド API: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "📋 ログを確認するには:"
echo "   docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
