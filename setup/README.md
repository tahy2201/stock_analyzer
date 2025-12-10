# Raspberry Pi 初回セットアップガイド

このディレクトリには、Raspberry Piへの自動デプロイシステムの初回セットアップに必要なファイルが含まれています。

## 概要

GitHubでタグまたはリリースを作成すると、Webhookを通じてRaspberry Piに自動デプロイされるシステムをセットアップします。

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
git clone <リポジトリURL> stock_analyzer
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

### 3. Webhook Secretの生成

強力なランダム文字列を生成します：

```bash
openssl rand -hex 32
```

このシークレットは後で使用するので、メモしておいてください。

### 4. systemdサービスファイルの編集

`setup/stock-deploy-webhook.service` を編集し、`WEBHOOK_SECRET` を設定します：

```bash
nano setup/stock-deploy-webhook.service
```

以下の行を変更：
```ini
Environment="WEBHOOK_SECRET=CHANGE_THIS_SECRET"
```

↓

```ini
Environment="WEBHOOK_SECRET=<手順3で生成したシークレット>"
```

ユーザー名（`User=rp-tahy`）も必要に応じて変更してください。

### 5. スクリプトに実行権限を付与

```bash
chmod +x setup/webhook_server.py
```

### 6. systemdサービスの登録

```bash
# サービスファイルをコピー
sudo cp setup/stock-deploy-webhook.service /etc/systemd/system/

# systemdを再読み込み
sudo systemctl daemon-reload

# サービスを有効化（自動起動設定）
sudo systemctl enable stock-deploy-webhook

# サービスを開始
sudo systemctl start stock-deploy-webhook

# ステータス確認
sudo systemctl status stock-deploy-webhook
```

### 7. ログディレクトリの作成

```bash
mkdir -p ~/logs
```

### 8. GitHub Webhookの設定

1. GitHubリポジトリページを開く
2. **Settings** → **Webhooks** → **Add webhook** をクリック
3. 以下の情報を入力：
   - **Payload URL**: `http://<ラズパイのIPアドレス>:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: 手順3で生成したシークレット
   - **Which events would you like to trigger this webhook?**:
     - "Let me select individual events" を選択
     - **Pushes** と **Releases** にチェック
4. **Add webhook** をクリック

### 9. 動作確認

テスト用のタグを作成してデプロイを確認します：

```bash
# 開発機で
git tag v0.0.1
git push origin v0.0.1
```

Raspberry Pi側でログを確認：

```bash
# サービスのログを確認
sudo journalctl -u stock-deploy-webhook -f

# または、デプロイログファイルを確認
tail -f ~/logs/deploy.log
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
├── webhook_server.py              # Webhookサーバースクリプト
├── stock-deploy-webhook.service   # systemdサービスファイル
├── migrate-db-to-prod.sh          # 初回DB移行スクリプト（オプション）
└── README.md                      # このファイル
```

## 次のステップ

初回セットアップが完了したら、以下のドキュメントを参照してください：

- [DEPLOYMENT.md](../DEPLOYMENT.md) - デプロイ方法と運用ガイド
- [scripts/](../scripts/) - 開発用補助スクリプト

## トラブルシューティング

セットアップ中に問題が発生した場合は、[DEPLOYMENT.md](../DEPLOYMENT.md) のトラブルシューティングセクションを参照してください。
