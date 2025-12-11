# Cron初回設定ガイド

Raspberry Piで定期バッチ処理を実行するための初回セットアップ手順です。

## 前提条件

- [初回セットアップ](README.md)が完了していること
- Dockerコンテナが起動していること

## セットアップ手順

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

## 次のステップ

初回設定が完了したら、以下のドキュメントを参照してください：

- [Cron運用ガイド](../backend/cron/README.md) - バッチ処理の詳細と運用方法
- [DEPLOYMENT.md](../DEPLOYMENT.md) - デプロイ方法と運用ガイド
