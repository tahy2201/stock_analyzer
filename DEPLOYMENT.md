# デプロイメントガイド

Stock Analyzerを本番環境（Raspberry Pi）にデプロイする方法について説明します。

## 前提条件

- [初回セットアップ](setup/README.md)が完了していること
- Webhookサーバーが稼働していること

## デプロイ方法

GitHubでタグを作成してpushすると、Webhookを通じてRaspberry Piに自動デプロイされます。

```bash
# バージョンタグを作成
git tag v1.0.0

# タグをpush
git push origin v1.0.0
```

タグをpushすると自動的にデプロイが開始されます。

### リリースノートを追加する場合（オプション）

デプロイ後に、必要に応じてGitHubでリリースノートを追加できます：

```bash
# GitHub CLI を使用
gh release create v1.0.0 --title "Version 1.0.0" --notes "バグ修正とパフォーマンス改善"
```

または、GitHub Web UIで **Releases** → **Create a new release** から作成できます。

## デプロイの確認

### ログの確認

```bash
# Raspberry Piにログイン
ssh rp-tahy@raspberrypi

# リアルタイムでログを確認
sudo journalctl -u stock-deploy-webhook -f

# 最新100行を表示
sudo journalctl -u stock-deploy-webhook -n 100

# デプロイログファイルを確認
cat ~/logs/deploy.log
```

### コンテナの状態確認

```bash
# Raspberry Piで実行
cd ~/stock_analyzer
docker compose -f docker-compose.prod.yml ps
```

### アプリケーションの動作確認

ブラウザで以下のURLにアクセスして動作を確認します：

- フロントエンド: `http://<ラズパイのIPアドレス>:4173`
- バックエンドAPI: `http://<ラズパイのIPアドレス>:8000/docs`

## サービスの管理

### Webhookサーバーの管理

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

### アプリケーションコンテナの管理

```bash
# Raspberry Piで実行
cd ~/stock_analyzer

# コンテナの再起動
docker compose -f docker-compose.prod.yml restart

# コンテナの停止
docker compose -f docker-compose.prod.yml down

# コンテナの起動
docker compose -f docker-compose.prod.yml up -d

# コンテナの再ビルド
docker compose -f docker-compose.prod.yml up -d --build
```

## トラブルシューティング

### Webhookが届かない

1. **Raspberry Piのファイアウォール設定を確認**
   ```bash
   sudo ufw status
   ```

2. **ルーターのポートフォワーディング設定を確認**
   - 9000番ポートが開放されているか確認

3. **GitHubのWebhook設定ページで配信履歴を確認**
   - Settings → Webhooks → Recent Deliveries

### デプロイが失敗する

**ログを確認して原因を特定：**

```bash
sudo journalctl -u stock-deploy-webhook -n 200
```

**よくある原因：**

- **Dockerコマンドの実行失敗**
  ```bash
  docker --version
  docker compose version
  ```

- **Gitコマンドの実行失敗**
  ```bash
  cd ~/stock_analyzer
  git status
  git remote -v
  ```

- **環境変数の設定ミス**
  ```bash
  cat ~/stock_analyzer/.env
  ```

### サービスが起動しない

```bash
# 詳細なログを確認
sudo journalctl -u stock-deploy-webhook -xe

# 手動でスクリプトを実行してエラーを確認
cd ~/stock_analyzer/setup
export WEBHOOK_SECRET='your-secret'
python3 webhook_server.py
```

### ディスク容量不足

```bash
# 全体のディスク使用量
df -h

# プロジェクトディレクトリのサイズ
du -sh ~/stock_analyzer

# Dockerが使用している容量
docker system df

# 不要なDockerリソースを削除
docker system prune -a
```

## セキュリティ

### Webhook Secret

- 絶対に公開しないでください
- 定期的に変更することを推奨

### ファイアウォール設定

9000番ポートへのアクセスをGitHubのIPアドレス範囲のみに制限することを推奨：

```bash
# 例: 特定のIPアドレスからのみ許可
sudo ufw allow from <GitHub IP範囲> to any port 9000
sudo ufw enable
```

### HTTPS通信

可能であればリバースプロキシ（nginx等）を使用してHTTPSで通信することを推奨します。

## 関連ドキュメント

- [初回セットアップ](setup/README.md) - Raspberry Piの初期設定
- [開発用スクリプト](scripts/) - データ同期などの補助スクリプト
