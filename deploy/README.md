# Stock Analyzer Deployment Setup

このディレクトリには、Raspberry Piへの自動デプロイに必要なファイルが含まれています。

## 概要

GitHubでタグまたはリリースを作成すると、Webhookを通じてRaspberry Piに自動デプロイされます。

## セットアップ手順

### 1. リポジトリのクローン

Raspberry Piにログインし、リポジトリをクローンします：

```bash
ssh rp-tahy@raspberrypi
cd ~
git clone <リポジトリURL> stock_analyzer
cd stock_analyzer
```

### 2. Webhook Secretの生成

強力なランダム文字列を生成します：

```bash
openssl rand -hex 32
```

このシークレットは後で使用するので、メモしておいてください。

### 3. systemdサービスファイルの編集

`deploy/stock-deploy-webhook.service` を編集し、`WEBHOOK_SECRET` を設定します：

```bash
nano deploy/stock-deploy-webhook.service
```

以下の行を変更：
```ini
Environment="WEBHOOK_SECRET=CHANGE_THIS_SECRET"
```

↓

```ini
Environment="WEBHOOK_SECRET=あなたが生成したシークレット"
```

ユーザー名やパスも必要に応じて変更してください。

### 4. スクリプトに実行権限を付与

```bash
chmod +x deploy/webhook_server.py
```

### 5. systemdサービスの登録

```bash
# サービスファイルをコピー
sudo cp deploy/stock-deploy-webhook.service /etc/systemd/system/

# systemdを再読み込み
sudo systemctl daemon-reload

# サービスを有効化（自動起動設定）
sudo systemctl enable stock-deploy-webhook

# サービスを開始
sudo systemctl start stock-deploy-webhook

# ステータス確認
sudo systemctl status stock-deploy-webhook
```

### 6. GitHub Webhookの設定

1. GitHubリポジトリページを開く
2. **Settings** → **Webhooks** → **Add webhook** をクリック
3. 以下の情報を入力：
   - **Payload URL**: `http://<ラズパイのIPアドレス>:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: 手順2で生成したシークレット
   - **Which events would you like to trigger this webhook?**:
     - "Let me select individual events" を選択
     - **Pushes** と **Releases** にチェック
4. **Add webhook** をクリック

### 7. 動作確認

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
tail -f ~/deploy/deploy.log
```

## 日常的な使い方

### デプロイ方法

**方法1: タグを作成してpush**

```bash
git tag v1.0.0
git push origin v1.0.0
```

**方法2: GitHubでリリースを作成**

1. GitHubリポジトリページで **Releases** をクリック
2. **Create a new release** をクリック
3. タグ名を入力（例: `v1.0.0`）
4. リリース内容を記入
5. **Publish release** をクリック

どちらの方法でも、自動的にRaspberry Piにデプロイされます。

### ログの確認

```bash
# リアルタイムでログを確認
sudo journalctl -u stock-deploy-webhook -f

# 最新100行を表示
sudo journalctl -u stock-deploy-webhook -n 100

# デプロイログファイルを確認
cat ~/deploy/deploy.log
```

### サービスの管理

```bash
# サービスの状態確認
sudo systemctl status stock-deploy-webhook

# サービスの再起動
sudo systemctl restart stock-deploy-webhook

# サービスの停止
sudo systemctl stop stock-deploy-webhook

# サービスの開始
sudo systemctl start stock-deploy-webhook
```

## トラブルシューティング

### Webhookが届かない

1. Raspberry Piのファイアウォール設定を確認
2. ルーターのポートフォワーディング設定を確認（9000番ポート）
3. GitHubのWebhook設定ページで配信履歴を確認

### デプロイが失敗する

ログを確認して原因を特定：

```bash
sudo journalctl -u stock-deploy-webhook -n 200
```

よくある原因：
- Dockerコマンドの実行失敗 → Dockerが正常に動作しているか確認
- Gitコマンドの実行失敗 → リポジトリの状態を確認
- 環境変数の設定ミス → `.env` ファイルを確認

### サービスが起動しない

```bash
# 詳細なログを確認
sudo journalctl -u stock-deploy-webhook -xe

# 手動でスクリプトを実行してエラーを確認
cd ~/stock_analyzer/deploy
export WEBHOOK_SECRET='your-secret'
python3 webhook_server.py
```

## セキュリティ上の注意

- **Webhook Secret**: 絶対に公開しないでください
- **ファイアウォール**: 9000番ポートへのアクセスをGitHubのIPアドレス範囲のみに制限することを推奨
- **HTTPS**: 可能であればリバースプロキシ（nginx等）を使用してHTTPSで通信

## ファイル構成

```
deploy/
├── webhook_server.py              # Webhookサーバースクリプト
├── stock-deploy-webhook.service   # systemdサービスファイル
└── README.md                      # このファイル
```

## 関連ファイル

- [docker-compose.prod.yml](../docker-compose.prod.yml) - 本番環境用Docker Compose設定
- [.github/workflows/deploy-to-raspi.yml](../.github/workflows/deploy-to-raspi.yml) - 旧GitHub Actionsワークフロー（参考用）
