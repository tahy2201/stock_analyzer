#!/bin/bash
# ローカルから簡単にデプロイできるスクリプト

set -e

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Stock Analyzer Deployment Tool${NC}"
echo ""

# デプロイ方法を選択
echo "Select deployment method:"
echo "  1) Create Git Tag (recommended)"
echo "  2) Create GitHub Release"
echo "  3) Trigger GitHub Actions manually"
echo "  4) Direct deploy to Raspberry Pi"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
  1)
    # Git Tag
    echo -e "${BLUE}📝 Creating Git Tag${NC}"
    echo ""

    # 現在のバージョンを取得
    CURRENT_VERSION=$(git tag --sort=-v:refname | head -n 1)
    echo "Current version: ${CURRENT_VERSION:-none}"
    echo ""

    read -p "Enter new version (e.g., v1.0.0): " VERSION

    if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo -e "${RED}❌ Invalid version format. Use v1.0.0 format${NC}"
      exit 1
    fi

    read -p "Enter tag message: " MESSAGE

    echo ""
    echo -e "${YELLOW}Creating tag: $VERSION${NC}"
    git tag -a "$VERSION" -m "$MESSAGE"

    echo -e "${YELLOW}Pushing tag to remote...${NC}"
    git push origin "$VERSION"

    echo ""
    echo -e "${GREEN}✅ Tag created and pushed!${NC}"
    echo -e "${GREEN}GitHub Actions will automatically deploy to Raspberry Pi${NC}"
    echo ""
    echo "Monitor deployment:"
    echo "  https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:\/]\(.*\)\.git/\1/')/actions"
    ;;

  2)
    # GitHub Release
    echo -e "${BLUE}📦 Creating GitHub Release${NC}"
    echo ""

    # ghコマンドの確認
    if ! command -v gh &> /dev/null; then
      echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
      echo "Install: https://cli.github.com/"
      exit 1
    fi

    # 現在のバージョンを取得
    CURRENT_VERSION=$(git tag --sort=-v:refname | head -n 1)
    echo "Current version: ${CURRENT_VERSION:-none}"
    echo ""

    read -p "Enter release version (e.g., v1.0.0): " VERSION

    if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo -e "${RED}❌ Invalid version format. Use v1.0.0 format${NC}"
      exit 1
    fi

    read -p "Enter release title: " TITLE
    read -p "Generate release notes automatically? [Y/n]: " AUTO_NOTES

    if [[ "$AUTO_NOTES" =~ ^[Nn] ]]; then
      read -p "Enter release notes: " NOTES
      gh release create "$VERSION" --title "$TITLE" --notes "$NOTES"
    else
      gh release create "$VERSION" --title "$TITLE" --generate-notes
    fi

    echo ""
    echo -e "${GREEN}✅ Release created!${NC}"
    echo -e "${GREEN}GitHub Actions will automatically deploy to Raspberry Pi${NC}"
    ;;

  3)
    # GitHub Actions手動実行
    echo -e "${BLUE}🔧 Triggering GitHub Actions${NC}"
    echo ""

    # ghコマンドの確認
    if ! command -v gh &> /dev/null; then
      echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
      echo "Install: https://cli.github.com/"
      exit 1
    fi

    echo "Select environment:"
    echo "  1) production"
    echo "  2) staging"
    read -p "Enter choice [1-2]: " env_choice

    case $env_choice in
      1) ENVIRONMENT="production" ;;
      2) ENVIRONMENT="staging" ;;
      *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
    esac

    read -p "Enter deployment reason (optional): " REASON

    echo ""
    echo -e "${YELLOW}Triggering workflow...${NC}"

    if [ -n "$REASON" ]; then
      gh workflow run deploy-to-raspi.yml -f environment="$ENVIRONMENT" -f reason="$REASON"
    else
      gh workflow run deploy-to-raspi.yml -f environment="$ENVIRONMENT"
    fi

    echo ""
    echo -e "${GREEN}✅ Workflow triggered!${NC}"
    echo ""
    echo "Monitor deployment:"
    echo "  gh run watch"
    ;;

  4)
    # 直接デプロイ
    echo -e "${BLUE}🔌 Direct Deploy to Raspberry Pi${NC}"
    echo ""

    RASPI_USER="${PROD_RASPI_USER:-pi}"
    RASPI_IP="${PROD_RASPI_IP}"
    RASPI_PROJECT_DIR="${PROD_RASPI_PROJECT_DIR:-/home/${RASPI_USER}/stock_analyzer}"

    if [ -z "$RASPI_IP" ]; then
      read -p "Enter Raspberry Pi IP address: " RASPI_IP
    fi

    echo -e "${YELLOW}Connecting to ${RASPI_USER}@${RASPI_IP}...${NC}"

    ssh "${RASPI_USER}@${RASPI_IP}" << EOF
      set -e
      cd ${RASPI_PROJECT_DIR}

      echo "📥 Pulling latest changes..."
      git pull origin main

      echo "🛑 Stopping containers..."
      docker-compose -f docker-compose.prod.yml down || true

      echo "🔨 Building and starting containers..."
      source .env 2>/dev/null || true
      docker-compose -f docker-compose.prod.yml up -d --build

      echo "⏳ Waiting for services..."
      sleep 5

      echo "📊 Container status:"
      docker-compose -f docker-compose.prod.yml ps

      echo ""
      echo "✅ Deployment completed!"
EOF

    echo ""
    echo -e "${GREEN}✅ Direct deployment completed!${NC}"
    ;;

  *)
    echo -e "${RED}Invalid choice${NC}"
    exit 1
    ;;
esac

echo ""
echo -e "${BLUE}🎉 Deployment initiated successfully!${NC}"
