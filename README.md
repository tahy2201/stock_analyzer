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
cd backend
uv sync
```

### 3. データベース初期化
```bash
cd backend
uv run python -c "from shared.database.models import create_tables; create_tables()"
```

## 📊 使い方

### 🚀 データ更新

以下の処理を順に実行します。
- JPXからDLしたファイルの読み込み/DB登録
- 株価データ、企業情報の取得/更新
- 取得したデータから25日平均、配当利回りなどの計算

#### 起動

**JPXデータ取り込み**

**注意**: 事前にJPXの上場企業一覧Excelファイルを`data/`フォルダに配置してください。
- ダウンロード先: https://www.jpx.co.jp/markets/statistics-equities/misc/01.html

```bash
# JPXデータ更新（初回セットアップ時に実行）
uv run python batch/jpx_importer.py

# ログレベルを詳細にして実行
uv run python batch/jpx_importer.py -v
```

**基本実行**

```bash
# backend ディレクトリから実行
cd backend

# プライム市場の株価データ更新
uv run python batch/stock_updater.py --markets prime

# 特定銘柄の株価データ更新
uv run python batch/stock_updater.py --symbols 7203 6758

# スタンダード市場の株価データ更新
uv run python batch/stock_updater.py --markets standard
```

#### ヘルプ
```bash
# 各機能のヘルプ
uv run python batch/jpx_importer.py --help
uv run python batch/stock_updater.py --help
```

**ログ出力について**: click_logを使用しており、`-v`オプションで詳細なログが確認できます。

### 🚀 APIサーバー起動

FastAPIサーバーを起動して、フロントエンドからアクセス可能にします。

```bash
# backend ディレクトリから実行
cd backend

# APIサーバー起動
uv run python -m api.main
```

サーバーは http://localhost:8000 で起動します。

### 🎨 フロントエンド起動

React + Vite + TypeScript で構築されたフロントエンドアプリケーションを起動します。

```bash
# frontend ディレクトリから実行
cd frontend

# 依存関係のインストール（初回のみ）
bun install

# 開発サーバー起動
bun run dev
```

フロントエンドは http://localhost:5173 で起動します。

**注意**: フロントエンドを使用する場合は、事前にAPIサーバーを起動しておく必要があります。

## 📄 ログ出力について

### ログレベルとオプション

各バッチ処理は詳細なログ出力に対応しており、実行状況を確認できます。

```bash
# 通常実行（INFOレベル）
uv run python batch/stock_updater.py --symbols 7203

# 詳細ログ出力（DEBUGレベル）
uv run python batch/jpx_importer.py -v

# 極めて詳細なログ出力
uv run python batch/jpx_importer.py -vv
```

**ログファイル**: 各バッチのログは `logs/` ディレクトリに保存されます。
- `logs/batch.log` - バッチ処理ログ
- `logs/jpx.log` - JPX取り込みログ
- `logs/api.log` - APIサーバーログ

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
│   │   ├── stock_updater.py        # 株価更新CLI（click対応）
│   │   └── jpx_importer.py         # JPX取り込みCLI（click対応）
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
│   ├── mypy.ini              # mypy設定
│   └── pyproject.toml        # プロジェクト設定
├── front/                    # React + TypeScript + Vite フロントエンド
│   ├── src/
│   │   ├── components/       # Reactコンポーネント
│   │   ├── pages/            # ページコンポーネント
│   │   └── services/         # API呼び出し
│   └── package.json          # Node.js依存関係
├── .vscode/                  # VSCode設定
├── config/                   # デプロイメント設定
└── README.md                 # このファイル
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