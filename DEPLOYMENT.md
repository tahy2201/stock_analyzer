# デプロイメントガイド

Stock Analyzerを本番環境（Raspberry Pi）にデプロイする方法について説明します。

## 前提条件

- [初回セットアップ](setup/README.md)が完了していること
- Raspberry PiにSSH接続できること

## デプロイ方法

### 基本的なデプロイ手順

1. **開発機でタグを作成してpush**

```bash
# バージョンタグを作成
git tag v1.0.0

# タグをpush
git push origin v1.0.0
```

2. **Raspberry PiにSSH接続**

```bash
ssh rp-tahy@raspberrypi
cd ~/stock_analyzer  # または ~/work/tahy/stock_analyzer
```

3. **デプロイスクリプトを実行**

```bash
./deploy.sh
```

または、タグ名を引数で指定：

```bash
./deploy.sh v1.0.0
```

スクリプトは以下を自動的に実行します：

- 最新のタグを取得
- 指定されたタグにチェックアウト
- 既存のコンテナを停止
- 新しいコンテナをビルド
- コンテナを起動

### デプロイスクリプトの使い方

**対話モード（タグ名を指定しない場合）:**

```bash
./deploy.sh

# 利用可能なタグ一覧が表示されます
# デプロイするタグ名を入力してください
```

**直接指定モード:**

```bash
./deploy.sh v1.0.0
```

## デプロイの確認

### コンテナの状態確認

```bash
# Raspberry Piで実行
cd ~/stock_analyzer
docker compose -f docker-compose.prod.yml ps
```

### ログの確認

```bash
# リアルタイムでログを確認
docker compose -f docker-compose.prod.yml logs -f

# 特定のサービスのログのみ確認
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### アプリケーションの動作確認

ブラウザで以下のURLにアクセスして動作を確認します：

- フロントエンド: `http://<ラズパイのIPアドレス>:4173`
- バックエンドAPI: `http://<ラズパイのIPアドレス>:8000/docs`

## サービスの管理

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

### デプロイが失敗する

**タグが見つからない場合:**

```bash
# リモートのタグを確認
git fetch --tags
git tag -l

# 特定のタグが存在するか確認
git rev-parse v1.0.0
```

**Gitコマンドの実行失敗:**

```bash
cd ~/stock_analyzer
git status
git remote -v

# リモートリポジトリから最新を取得
git fetch --all --tags
```

**Dockerコマンドの実行失敗:**

```bash
# Dockerの状態を確認
docker --version
docker compose version

# Dockerサービスの状態を確認
sudo systemctl status docker

# Dockerサービスを再起動
sudo systemctl restart docker
```

**環境変数の設定ミス:**

```bash
# .envファイルを確認
cat ~/stock_analyzer/.env

# 必要に応じて再作成
cd ~/stock_analyzer
nano .env
```

### コンテナが起動しない

```bash
# コンテナのログを確認
docker compose -f docker-compose.prod.yml logs

# 詳細なエラー情報を確認
docker compose -f docker-compose.prod.yml ps -a
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
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

### ポート競合

```bash
# ポート8000と4173が使用されているか確認
sudo lsof -i :8000
sudo lsof -i :4173

# 必要に応じてプロセスを停止
sudo kill <PID>
```

## ロールバック

問題が発生した場合、以前のバージョンに戻すことができます：

```bash
# 以前のタグにロールバック
./deploy.sh v0.9.0
```

## データベース管理

### 本番環境から開発環境へのDB同期

```bash
# 開発機で実行
PROD_RASPI_IP=<ラズパイのIPアドレス> \
PROD_RASPI_USER=rp-tahy \
./scripts/sync-db-from-prod.sh
```

### データベースのバックアップ

```bash
# Raspberry Piで実行
cd ~/stock_analyzer
cp data/stock_data.db data/stock_data.db.backup.$(date +%Y%m%d_%H%M%S)
```

## セキュリティ

### SSHアクセス

- SSH鍵認証を使用してください
- パスワード認証は無効化することを推奨

### ファイアウォール設定

必要なポートのみ開放してください：

```bash
# SSH（22番ポート）
sudo ufw allow 22/tcp

# アプリケーション（ローカルネットワークのみ）
sudo ufw allow from 192.168.0.0/24 to any port 8000
sudo ufw allow from 192.168.0.0/24 to any port 4173

# ファイアウォールを有効化
sudo ufw enable
```

## 関連ドキュメント

- [初回セットアップ](setup/README.md) - Raspberry Piの初期設定
- [開発用スクリプト](scripts/) - データ同期などの補助スクリプト
