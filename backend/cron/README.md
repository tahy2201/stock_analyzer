# Cron運用ガイド

本番環境で稼働中のバッチ処理の運用方法について説明します。

## バッチ処理の種類

1. **株価データ更新** (`run-stock-updater.sh`)
   - 全銘柄の株価データを更新
   - 実行時間: 毎日12:00と24:00（0:00）
   - ログ: `~/logs/stock-updater.log`

2. **JPX企業リスト更新** (`run-jpx-importer.sh`)
   - JPXから最新の企業リストをインポート
   - 実行時間: 毎月15日 9:30
   - ログ: `~/logs/jpx-importer.log`
   - **15日にした理由**: JPXは「毎月第3営業日の午前9時以降に前月末データを掲載」しますが、GWなど連休により第3営業日が大きくずれる可能性があります（例: 2026年5月は第3営業日が11日）。15日であれば、どの月でも確実に第3営業日以降となるため、この日付を選択しています。

## ログの確認

```bash
# 株価データ更新ログ
tail -f ~/logs/stock-updater.log

# JPX企業リストインポートログ
tail -f ~/logs/jpx-importer.log
```

## 手動実行

緊急時やテスト時に手動でバッチを実行できます：

```bash
cd ~/work/tahy/stock_analyzer

# 株価データ更新
./backend/cron/run-stock-updater.sh

# JPX企業リストインポート
./backend/cron/run-jpx-importer.sh
```

## Cron設定の確認・変更

### 現在の設定を確認

```bash
crontab -l
```

### 設定を編集

```bash
crontab -e
```

### Cron時刻フォーマット

```
分 時 日 月 曜日 コマンド
```

例：
- `0 12 * * *` - 毎日12:00
- `30 9 15 * *` - 毎月15日 9:30
- `0 */6 * * *` - 6時間ごと
- `0 9 * * 1` - 毎週月曜日 9:00

### 株価データ更新頻度を変更する場合

```cron
# 例: 6時間ごとに実行
0 */6 * * * /home/rp-tahy/work/tahy/stock_analyzer/backend/cron/run-stock-updater.sh
```

## トラブルシューティング

### バッチが実行されない

1. **Cron設定を確認**
   ```bash
   crontab -l
   ```

2. **スクリプトの実行権限を確認**
   ```bash
   ls -la ~/work/tahy/stock_analyzer/backend/cron/run-*.sh
   ```

3. **Cronのログを確認**
   ```bash
   sudo grep CRON /var/log/syslog | tail -20
   ```

### Dockerコンテナが起動していない

バッチ実行前にDockerコンテナが起動している必要があります：

```bash
cd ~/work/tahy/stock_analyzer
docker compose -f docker-compose.prod.yml ps
```

停止している場合は起動してください：

```bash
docker compose -f docker-compose.prod.yml up -d
```

### パス指定のミス

cronは限られた環境変数しか持たないため、スクリプト内で絶対パスを使用しています。
`~/`は展開されないので、`/home/rp-tahy/`のように絶対パスで指定してください。

### バッチ実行中のエラー

ログファイルでエラー内容を確認：

```bash
# 最新のエラーを確認
tail -50 ~/logs/stock-updater.log
tail -50 ~/logs/jpx-importer.log

# エラー行のみ抽出
grep ERROR ~/logs/stock-updater.log
```

## ログローテーション（推奨）

ログファイルが肥大化するのを防ぐため、logrotateを設定することを推奨します：

```bash
sudo nano /etc/logrotate.d/stock-analyzer
```

以下の内容を追加：

```
/home/rp-tahy/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## セキュリティ

- ログファイルには機密情報が含まれる可能性があるため、適切な権限で保護してください
- 定期的にログファイルを確認し、異常がないかチェックしてください

## 関連ドキュメント

- [初回Cron設定](../../setup/cron-setup.md) - Cronの初回セットアップ手順
- [DEPLOYMENT.md](../../DEPLOYMENT.md) - デプロイ方法と運用ガイド
