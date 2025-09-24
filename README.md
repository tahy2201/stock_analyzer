# 株式分析システム

日本株から投資候補を効率的に抽出するシステムです。バッチ処理でデータ取得・分析を行い、技術分析に基づいて投資候補を抽出します。

## 📋 システム要件

- Python 3.9+
- インターネット接続（株価データ取得用）
- 約1GB のディスク容量（全銘柄データ保存用）

## 🛠️ インストール

### 1. リポジトリのクローン
```bash
git clone https://github.com/tahy2201/stock_analyzer.git
cd stock_analyzer
```

### 2. 依存関係のインストール
```bash
uv sync
```

### 3. データベース初期化
```bash
uv run python -c "from database.models import create_tables; create_tables()"
```

## 📊 使い方

### 🚀 データ更新

以下の処理を順に実行します。
- JPXからDLしたファイルの読み込み/DB登録
- 株価データ、企業情報の取得/更新
- 取得したデータから25日平均、配当利回りなどの計算

#### 起動
```bash
# プライム市場のエンタープライズ企業のみ
python backend/batch/stock_updater.py --markets prime

# 日次更新（推奨）
python backend/batch/stock_updater.py --mode daily

# 完全更新（初回またはデータリセット時）
python backend/batch/stock_updater.py --mode full
```

#### オプション
```bash
# 複数銘柄指定
python backend/batch/stock_updater.py --symbols 7203,6758,9984

# 市場区分指定
python backend/batch/stock_updater.py --markets prime,standard,growth

# JPXデータ更新をスキップ
python backend/batch/stock_updater.py --symbols 7203 --skip-jpx

# エンタープライズ企業のみ処理
python backend/batch/stock_updater.py --enterprise-only
```

#### ヘルプ
```bash
python backend/batch/stock_updater.py --help
```

### 🏢 JPXファイル取り込み（初回セットアップ）

JPX（日本取引所グループ）の上場企業一覧を取り込みます。通常は初回のみ実行します。

```bash
# JPXファイル取り込み（初回セットアップ時）
python backend/batch/jpx_importer.py
```

**注意**: 事前にJPXの上場企業一覧Excelファイルを`data/`フォルダに配置してください。
- ダウンロード先: https://www.jpx.co.jp/markets/statistics-equities/misc/01.html

## 📈 データ構造

### データベーステーブル

#### companies テーブル
- `symbol`: 銘柄コード（例: 7203）
- `name`: 企業名
- `sector`: 業種
- `market`: 市場区分
- `employees`: 従業員数
- `revenue`: 売上高
- `is_enterprise`: エンタープライズ企業フラグ

#### stock_prices テーブル
- `symbol`: 銘柄コード
- `date`: 日付
- `open`, `high`, `low`, `close`: 四本値
- `volume`: 出来高

#### technical_indicators テーブル
- `symbol`: 銘柄コード
- `date`: 日付
- `ma_25`: 25日移動平均
- `divergence_rate`: 乖離率（%）
- `dividend_yield`: 配当利回り（%）
- `volume_avg_20`: 20日平均出来高

## 📁 ディレクトリ構成
```
stock_analyzer/
├── backend/                  # バックエンドシステム
│   ├── api/                  # FastAPI アプリケーション
│   │   ├── main.py           # APIメインエントリーポイント
│   │   └── routers/          # APIルーター
│   ├── batch/                # バッチ処理
│   │   └── batch_runner.py   # 統合バッチ処理
│   ├── services/             # サービス層（Rails風）
│   │   ├── analysis/         # 技術分析サービス
│   │   ├── data/             # データ収集サービス
│   │   ├── filtering/        # フィルタリングサービス
│   │   └── jpx/              # JPXデータ処理サービス
│   ├── shared/               # 共通モジュール
│   │   ├── config/           # 設定・モデル
│   │   ├── database/         # データベース管理
│   │   ├── jpx/              # JPXパーサー
│   │   └── utils/            # ユーティリティ
│   └── run_batch.py          # バッチ処理エントリーポイント
├── front/                    # React + TypeScript + Vite フロントエンド
│   ├── src/
│   │   ├── components/       # Reactコンポーネント
│   │   ├── pages/            # ページコンポーネント
│   │   └── services/         # API呼び出し
│   └── package.json          # Node.js依存関係
├── config/                   # 設定ファイル（共通）
├── database/                 # データベース関連（共通）
└── utils/                    # ユーティリティ（共通）
```

## 📝 注意事項

### 利用制限・免責事項

1. **データソース**: yfinanceを使用しているため、Yahoo Financeの利用規約に従ってください
2. **投資判断**: このシステムは投資の参考情報を提供するものであり、投資判断は自己責任で行ってください
3. **データ精度**: 株価データやメタデータの正確性は保証されません
4. **個人利用**: 個人利用を想定しており、商用利用時は追加考慮が必要です

### パフォーマンス

- **全銘柄データ取得**: 初回は30-60分程度
- **日次更新**: 10-20分程度
- **技術分析**: 1000銘柄で5-10分程度

## 🤝 コントリビューション

改善提案やバグ報告は Issue または Pull Request でお願いします。

## 📄 ライセンス

MIT License - 詳細は LICENSE ファイルを参照してください。

## 📚 参考資料

- [yfinance documentation](https://pypi.org/project/yfinance/)
- [JPX（日本取引所グループ）](https://www.jpx.co.jp/)
- [pandas documentation](https://pandas.pydata.org/)
- [SQLite documentation](https://www.sqlite.org/)

## 🔄 更新履歴

### v1.0.0 (2025-09-01)
- 初回リリース
- 基本的なデータ収集・技術分析・投資候補抽出機能
- バッチ処理システム
- SQLiteデータベース対応
- GitHub CLI統合
- 型安全性の改善（List[str] = None → List[str] = []）