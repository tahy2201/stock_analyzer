# デプロイメントガイド

このドキュメントでは、Stock Analyzerを本番環境（Raspberry Pi）にデプロイする手順を説明します。

## 📋 前提条件

- Raspberry Pi（Raspberry Pi 4推奨、RAM 4GB以上）
- Raspberry Pi OS（64-bit推奨）
- 固定IPアドレスが設定済み
- SSH接続が可能
- Dockerがインストール済み
- Git がインストール済み

## 🚀 初回セットアップ

### 1. Raspberry Piの準備

#### 1.1 Dockerのインストール

```bash
# ラズパイにSSH接続
ssh pi@192.168.1.100

# Dockerのインストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Composeのインストール
sudo apt-get install -y docker-compose

# ログアウト・ログインして設定を反映
exit
ssh pi@192.168.1.100

# Dockerの動作確認
docker --version
docker-compose --version
```

#### 1.2 プロジェクトのクローン

```bash
# プロジェクトディレクトリに移動
cd ~
git clone https://github.com/tahy2201/stock_analyzer.git
cd stock_analyzer
```

### 2. GitHub Secretsの設定

GitHubリポジトリに以下のSecretsを設定します。

**Settings > Secrets and variables > Actions > New repository secret**

| Secret名 | 値の例 | 説明 |
|---------|--------|------|
| `PROD_RASPI_IP` | `192.168.1.100` | ラズパイの固定IP |
| `PROD_RASPI_USER` | `pi` | SSH接続用ユーザー名 |
| `PROD_BACKEND_URL` | `http://192.168.1.100:8000` | バックエンドURL |
| `PROD_FRONTEND_URL` | `http://192.168.1.100:4173` | フロントエンドURL |

### 3. GitHub Actions Self-hosted Runnerのセットアップ

#### 3.1 GitHubでトークンを取得

1. GitHubリポジトリにアクセス
2. **Settings > Actions > Runners > New self-hosted runner**
3. 表示されたトークンをコピー

#### 3.2 ラズパイでRunnerをセットアップ

開発マシンから実行：

```bash
# 環境変数を設定してスクリプトを実行
GITHUB_REPO=tahy2201/stock_analyzer \
GITHUB_TOKEN=<GitHubで取得したトークン> \
ssh pi@192.168.1.100 'bash -s' < scripts/setup-raspi-runner.sh
```

または、ラズパイに直接接続して実行：

```bash
ssh pi@192.168.1.100
cd ~/stock_analyzer

export GITHUB_REPO=tahy2201/stock_analyzer
export GITHUB_TOKEN=<GitHubで取得したトークン>
./scripts/setup-raspi-runner.sh
```

#### 3.3 Runnerの確認

GitHubリポジトリの **Settings > Actions > Runners** で、ラズパイのRunnerがオンラインになっていることを確認します。

### 4. 環境変数の設定

ラズパイに環境変数ファイルを作成します。

```bash
# 開発マシンから実行
PROD_RASPI_IP=192.168.1.100 \
PROD_RASPI_USER=pi \
./scripts/setup-raspi-env.sh
```

または、ラズパイで直接作成：

```bash
ssh pi@192.168.1.100
cd ~/stock_analyzer

cat > .env << 'EOF'
PROD_API_BASE_URL=http://192.168.1.100:8000/api
PROD_FRONTEND_URL=http://192.168.1.100:4173
PROD_BACKEND_URL=http://192.168.1.100:8000
EOF
```

### 5. データベースの移行

開発環境の既存データを本番環境に移行します。

```bash
# 開発マシンで実行
PROD_RASPI_IP=192.168.1.100 \
PROD_RASPI_USER=pi \
./scripts/migrate-db-to-prod.sh
```

### 6. 初回デプロイ

GitHubにpushすると自動的にデプロイされます。

```bash
git push origin main
```

または、手動でデプロイ：

```bash
# ラズパイで実行
ssh pi@192.168.1.100
cd ~/stock_analyzer
source .env
docker-compose -f docker-compose.prod.yml up -d --build
```

### 7. 動作確認

ブラウザで以下のURLにアクセスして動作を確認します。

- フロントエンド: `http://192.168.1.100:4173`
- バックエンドAPI: `http://192.168.1.100:8000/docs`

## 🔄 日常運用

### デプロイ方法

デプロイは以下の4つの方法から選択できます。

#### 方法1: デプロイスクリプトを使用（最も簡単）✨

```bash
# 対話形式でデプロイ
./scripts/deploy.sh
```

スクリプトでは以下の方法を選択できます：
1. Git Tagを作成してデプロイ
2. GitHub Releaseを作成してデプロイ
3. GitHub Actionsを手動で実行
4. 直接ラズパイにデプロイ

#### 方法2: Git Tagでデプロイ（推奨）

```bash
# バージョンタグを作成
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

タグをpushすると自動的にデプロイが開始されます。

#### 方法3: GitHub Releaseでデプロイ

GitHub CLIを使用：
```bash
gh release create v1.0.0 --title "Version 1.0.0" --generate-notes
```

または、GitHubのWebUI:
1. **Releases > Create a new release**
2. タグを作成し、リリースノートを記入
3. **Publish release**

#### 方法4: GitHub Actionsを手動実行

GitHub CLI:
```bash
gh workflow run deploy-to-raspi.yml \
  -f environment=production \
  -f reason="Bug fix deployment"
```

または、GitHubのWebUI:
1. **Actions > Deploy to Raspberry Pi > Run workflow**
2. 環境とデプロイ理由を入力
3. **Run workflow**

#### 方法5: 直接ラズパイにSSH接続してデプロイ

```bash
ssh pi@192.168.1.100
cd ~/stock_analyzer
git pull origin main
source .env
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### データベースの同期

本番環境のデータを開発環境に同期します。

```bash
# 開発マシンで実行
PROD_RASPI_IP=192.168.1.100 \
PROD_RASPI_USER=pi \
./scripts/sync-db-from-prod.sh
```

## 📊 Cron設定（毎日のデータ更新）

ラズパイでcronを設定して、毎日自動的にデータを更新します。

```bash
# ラズパイで実行
ssh pi@192.168.1.100
crontab -e
```

以下を追加：

```cron
# 毎日朝6時にデータ更新
0 6 * * * cd /home/pi/stock_analyzer && docker-compose -f docker-compose.prod.yml exec -T backend python batch/stock_data_updater.py --markets prime >> /home/pi/logs/stock_update.log 2>&1

# 週次でDB最適化（日曜日3時）
0 3 * * 0 cd /home/pi/stock_analyzer && docker-compose -f docker-compose.prod.yml exec -T backend sqlite3 /app/data/stock_data.db 'VACUUM;' >> /home/pi/logs/db_vacuum.log 2>&1
```

ログディレクトリを作成：

```bash
mkdir -p ~/logs
```

## 🔧 トラブルシューティング

### コンテナの状態確認

```bash
ssh pi@192.168.1.100
cd ~/stock_analyzer
docker-compose -f docker-compose.prod.yml ps
```

### ログの確認

```bash
# 全体のログ
docker-compose -f docker-compose.prod.yml logs

# バックエンドのログのみ
docker-compose -f docker-compose.prod.yml logs backend

# フロントエンドのログのみ
docker-compose -f docker-compose.prod.yml logs frontend

# リアルタイムでログを追跡
docker-compose -f docker-compose.prod.yml logs -f
```

### コンテナの再起動

```bash
ssh pi@192.168.1.100
cd ~/stock_analyzer
docker-compose -f docker-compose.prod.yml restart
```

### コンテナの再ビルド

```bash
ssh pi@192.168.1.100
cd ~/stock_analyzer
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### GitHub Actions Runnerの確認

```bash
ssh pi@192.168.1.100
cd ~/actions-runner
sudo ./svc.sh status
```

Runnerが停止している場合：

```bash
sudo ./svc.sh start
```

### ディスク容量の確認

```bash
ssh pi@192.168.1.100

# 全体のディスク使用量
df -h

# プロジェクトディレクトリのサイズ
du -sh ~/stock_analyzer

# Dockerが使用している容量
docker system df
```

### 不要なDockerイメージ・コンテナの削除

```bash
# 停止中のコンテナを削除
docker container prune

# 未使用のイメージを削除
docker image prune -a

# 未使用のボリュームを削除
docker volume prune

# 全て一括削除（注意！）
docker system prune -a
```

## 🔐 セキュリティ

### ファイアウォールの設定（推奨）

家庭内ネットワークのみからアクセスを許可する設定例：

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw allow from 192.168.1.0/24 to any port 4173
sudo ufw enable
```

### SSH鍵認証の設定（推奨）

パスワード認証よりも安全です。

```bash
# 開発マシンで鍵を生成（未作成の場合）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 公開鍵をラズパイにコピー
ssh-copy-id pi@192.168.1.100
```

## 📚 参考資料

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Self-hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
