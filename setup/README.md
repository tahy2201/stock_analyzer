# Raspberry Pi 初回セットアップガイド

このディレクトリには、Raspberry Piへの初回セットアップに必要なファイルが含まれています。

## 概要

Stock Analyzerを本番環境（Raspberry Pi）で運用するための初回セットアップ手順を説明します。

## 前提条件

- Raspberry Pi（Raspberry Pi 4推奨、RAM 4GB以上）
- Raspberry Pi OS（64-bit推奨）
- 固定IPアドレスが設定済み
- SSH接続が可能
- Dockerがインストール済み
- Gitがインストール済み

## セットアップ手順

### 1. リポジトリのクローン

Raspberry Piにログインし、リポジトリをクローンします：

```bash
ssh rp-tahy@raspberrypi
cd ~
git clone https://github.com/tahy2201/stock_analyzer.git stock_analyzer
cd stock_analyzer
```

### 2. 環境変数ファイルの作成

本番用の `.env` ファイルを作成します：

```bash
cat > .env << 'ENVEOF'
PROD_API_BASE_URL=http://<ラズパイのIPアドレス>:8000/api
PROD_FRONTEND_URL=http://<ラズパイのIPアドレス>:4173
PROD_BACKEND_URL=http://<ラズパイのIPアドレス>:8000
ENVEOF
```

IPアドレスは実際のRaspberry PiのIPに置き換えてください。

### 3. デプロイスクリプトに実行権限を付与

```bash
chmod +x deploy.sh
```

### 4. 初回デプロイ

デプロイスクリプトを実行して、アプリケーションを起動します：

```bash
./deploy.sh
```

タグ名を入力するか、引数で指定できます：

```bash
./deploy.sh v1.0.0
```

デプロイが成功すれば、以下のURLでアプリケーションにアクセスできます：

- フロントエンド: `http://<ラズパイのIPアドレス>:4173`
- バックエンドAPI: `http://<ラズパイのIPアドレス>:8000/docs`

## 初回データ移行（オプション）

既存の開発環境のデータベースを本番環境に移行する場合：

```bash
# 開発機で実行
PROD_RASPI_IP=<ラズパイのIPアドレス> \
PROD_RASPI_USER=rp-tahy \
./setup/migrate-db-to-prod.sh
```

## Cron設定（定期バッチ処理）

定期的にデータを更新するため、cronを設定します。

### 1. ログディレクトリの作成

```bash
mkdir -p ~/logs
```

### 2. Crontabの編集

```bash
crontab -e
```

以下の内容を追加：

```cron
# Stock Analyzer バッチ処理

# 株価データ更新: 毎日12:00と24:00
0 12 * * * /home/rp-tahy/work/tahy/stock_analyzer/backend/cron/run-stock-updater.sh
0 0 * * * /home/rp-tahy/work/tahy/stock_analyzer/backend/cron/run-stock-updater.sh

# JPX企業リスト更新: 毎月15日 9:30
30 9 15 * * /home/rp-tahy/work/tahy/stock_analyzer/backend/cron/run-jpx-importer.sh
```

**重要**: パスは実際のRaspberry Piの環境に合わせて変更してください。

### 3. Cron設定の確認

```bash
crontab -l
```

### 4. 手動テスト実行

cron設定前に、手動でバッチを実行してテストしてください：

```bash
cd ~/work/tahy/stock_analyzer

# 株価データ更新
./backend/cron/run-stock-updater.sh

# JPX企業リストインポート
./backend/cron/run-jpx-importer.sh
```

ログファイルが `~/logs/` に作成され、正常に実行されることを確認してください。

## ファイル構成

```
setup/
├── migrate-db-to-prod.sh   # 初回DB移行スクリプト（オプション）
└── README.md               # このファイル
```

## 次のステップ

初回セットアップが完了したら、以下のドキュメントを参照してください：

- [DEPLOYMENT.md](../DEPLOYMENT.md) - デプロイ方法と運用ガイド
- [Cron運用ガイド](../backend/cron/README.md) - バッチ処理の運用方法
- [scripts/](../scripts/) - 開発用補助スクリプト

### テストユーザー作成

開発・テスト用のユーザーを作成するスクリプトを用意しています：

```bash
cd backend

# デフォルト（管理者 + 一般ユーザーの両方を作成）
uv run python ../scripts/seed_user.py

# カスタムユーザー作成
uv run python ../scripts/seed_user.py --login john --password YOUR_PASSWORD --display "John Doe" --role user

# 既存ユーザーの上書き更新
uv run python ../scripts/seed_user.py --login admin --password YOUR_PASSWORD --force
```

デフォルト実行で作成されるユーザー：
- **admin** / YOUR_PASSWORD (role: admin)
- **testuser** / YOUR_PASSWORD (role: user)

## トラブルシューティング

セットアップ中に問題が発生した場合は、[DEPLOYMENT.md](../DEPLOYMENT.md) のトラブルシューティングセクションを参照してください。
