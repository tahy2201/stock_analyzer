#!/bin/bash
# ラズパイにGitHub Actions Self-hosted Runnerをセットアップするスクリプト

set -e

echo "🔧 Setting up GitHub Actions Runner on Raspberry Pi..."

# 環境変数チェック
if [ -z "$GITHUB_REPO" ]; then
    echo "❌ Error: GITHUB_REPO environment variable is required"
    echo "Usage: GITHUB_REPO=tahy2201/stock_analyzer GITHUB_TOKEN=your_token ./setup-raspi-runner.sh"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GITHUB_TOKEN environment variable is required"
    echo "Get token from: https://github.com/$GITHUB_REPO/settings/actions/runners/new"
    exit 1
fi

# 作業ディレクトリ作成
RUNNER_DIR="$HOME/actions-runner"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# アーキテクチャ検出
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    RUNNER_ARCH="arm64"
elif [ "$ARCH" = "armv7l" ]; then
    RUNNER_ARCH="arm"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

# 最新のRunner バージョンを取得（または固定バージョンを使用）
RUNNER_VERSION="2.311.0"
RUNNER_FILE="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"

echo "📥 Downloading GitHub Actions Runner for $RUNNER_ARCH..."
curl -o "$RUNNER_FILE" -L "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}"

echo "📦 Extracting runner..."
tar xzf "$RUNNER_FILE"

echo "🔐 Configuring runner..."
./config.sh --url "https://github.com/$GITHUB_REPO" --token "$GITHUB_TOKEN" --name "raspi-runner" --work _work --labels raspi,self-hosted,linux,ARM64

echo "⚙️  Installing as a service..."
sudo ./svc.sh install

echo "🚀 Starting runner service..."
sudo ./svc.sh start

echo "✅ GitHub Actions Runner setup completed!"
echo ""
echo "📊 Check runner status:"
echo "   sudo ./svc.sh status"
echo ""
echo "🔗 Verify runner in GitHub:"
echo "   https://github.com/$GITHUB_REPO/settings/actions/runners"
