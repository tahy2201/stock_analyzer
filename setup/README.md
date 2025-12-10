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

## ファイル構成

```
setup/
├── migrate-db-to-prod.sh   # 初回DB移行スクリプト（オプション）
└── README.md               # このファイル
```

## 次のステップ

初回セットアップが完了したら、以下のドキュメントを参照してください：

- [DEPLOYMENT.md](../DEPLOYMENT.md) - デプロイ方法と運用ガイド
- [scripts/](../scripts/) - 開発用補助スクリプト

## トラブルシューティング

セットアップ中に問題が発生した場合は、[DEPLOYMENT.md](../DEPLOYMENT.md) のトラブルシューティングセクションを参照してください。
