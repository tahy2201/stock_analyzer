# 株式分析システム

日本株から投資候補を効率的に抽出するシステムです。バッチ処理でデータ取得・分析を行い、技術分析に基づいて投資候補を抽出します。

## 🚀 特徴

- **自動データ収集**: yfinanceを使った日本株の株価データ取得
- **技術分析**: 25日移動平均線、乖離率、配当利回りの計算
- **企業フィルタリング**: エンタープライズ企業の自動判定
- **市場分析**: 市場全体の過熱状況・トレンド分析
- **投資候補抽出**: 設定可能な条件による自動スクリーニング
- **SQLiteデータベース**: 軽量で管理しやすいデータストレージ

## 📋 システム要件

- Python 3.9+
- インターネット接続（株価データ取得用）
- 約1GB のディスク容量（全銘柄データ保存用）

## 🛠️ インストール

### 1. リポジトリのクローン
```bash
git clone <repository-url>
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

### 基本的な使い方

#### 1. 企業データの登録
```bash
# JPXデータ（手動ダウンロード後）
uv run python utils/jpx_parser.py

# またはテスト用サンプルデータ
uv run python -c "
import pandas as pd
from database.database_manager import DatabaseManager
test_data = [
    {'symbol': '7203', 'name': 'トヨタ自動車', 'sector': 'Transportation', 'market': 'プライム', 'is_enterprise': True},
    {'symbol': '6758', 'name': 'ソニーグループ', 'sector': 'Technology', 'market': 'プライム', 'is_enterprise': True}
]
db = DatabaseManager()
for company in test_data:
    db.insert_company(company)
"
```

#### 2. 株価データ収集
```bash
# 特定銘柄のデータ収集
uv run python batch/run_batch.py --mode data-only --symbols 7203,6758

# 全エンタープライズ企業のデータ収集
uv run python batch/run_batch.py --mode data-only
```

#### 3. 技術分析実行
```bash
# 特定銘柄の技術分析
uv run python batch/run_batch.py --mode analysis-only --symbols 7203,6758

# 全企業の技術分析
uv run python batch/run_batch.py --mode analysis-only
```

#### 4. 投資候補の抽出
```bash
uv run python -c "
from batch.technical_analyzer import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()
candidates = analyzer.get_investment_candidates()
for i, candidate in enumerate(candidates[:5]):
    print(f'{i+1}. {candidate[\"symbol\"]} ({candidate[\"name\"]}): 乖離率{candidate.get(\"divergence_rate\", 0):+.1f}%, 配当{candidate.get(\"dividend_yield\", 0):.1f}%')
"
```

### バッチ処理コマンド

#### 基本コマンド
```bash
# 日次更新（推奨）
uv run python batch/run_batch.py --mode daily

# 完全更新（初回またはデータリセット時）
uv run python batch/run_batch.py --mode full

# JPXデータ更新のみ
uv run python batch/run_batch.py --mode jpx-only

# 企業フィルタリングのみ
uv run python batch/run_batch.py --mode filter-only

# uvのscriptコマンドを使用（推奨）
uv run stock-analyzer --mode daily
```

#### オプション
```bash
# 特定銘柄のみ処理
uv run stock-analyzer --mode daily --symbols 7203,6758,9984

# JPXデータ更新をスキップ
uv run stock-analyzer --mode full --skip-jpx

# エンタープライズ企業のみ処理
uv run stock-analyzer --mode data-only --enterprise-only
```

### 各モジュールの個別実行

#### 株価データ収集
```python
from batch.data_collector import StockDataCollector
collector = StockDataCollector()

# 特定銘柄
results = collector.update_specific_stocks(['7203', '6758'])

# 全銘柄
results = collector.update_all_stocks()
```

#### 技術分析
```python
from batch.technical_analyzer import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()

# 技術分析実行
results = analyzer.analyze_batch_stocks(['7203', '6758'])

# 投資候補抽出
candidates = analyzer.get_investment_candidates(
    divergence_threshold=5.0,
    dividend_min=3.0,
    dividend_max=5.0
)
```

#### 市場分析
```python
from utils.market_analyzer import MarketAnalyzer
market_analyzer = MarketAnalyzer()

# 市場サマリー
summary = market_analyzer.get_market_summary()

# 過熱状況
overheated = market_analyzer.is_market_overheated()
```

## ⚙️ 設定

### config/settings.py での設定変更

```python
# 分析パラメータ
MA_PERIOD = 25                    # 移動平均期間
DIVERGENCE_THRESHOLD = 5.0        # 乖離率閾値（%）
DIVIDEND_YIELD_MIN = 3.0          # 配当利回り下限
DIVIDEND_YIELD_MAX = 5.0          # 配当利回り上限

# 企業規模フィルタ
MIN_EMPLOYEES = 1000              # 最小従業員数
MIN_REVENUE = 10_000_000_000      # 最小売上（100億円）

# データ取得設定
DATA_DAYS = 252                   # 取得日数（約1年）
BATCH_SIZE = 50                   # 並列処理バッチサイズ
YFINANCE_REQUEST_DELAY = 0.1      # APIリクエスト間隔（秒）
```

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

## 🔧 トラブルシューティング

### よくある問題

#### 1. yfinance でデータが取得できない
```bash
# 解決策: 時間を置いて再実行、またはシンボル形式を確認
uv run python -c "
import yfinance as yf
ticker = yf.Ticker('7203.T')
print(ticker.history(period='5d'))
"
```

#### 2. データベースエラー
```bash
# データベースを再作成
rm database/stock_data.db
uv run python -c "from database.models import create_tables; create_tables()"
```

#### 3. 投資候補が抽出されない
- 設定値を緩く調整
- データが十分に蓄積されているか確認
- 市場が過熱状態でないか確認

### ログの確認
```bash
# バッチ実行ログ
tail -f batch_log.txt

# Pythonでのデバッグ
uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# お使いのコードをここに
"
```

## 📁 ディレクトリ構成

```
stock_analyzer/
├── batch/                    # バッチ処理モジュール
│   ├── data_collector.py     # 株価データ収集
│   ├── technical_analyzer.py # 技術分析
│   ├── company_filter.py     # 企業フィルタリング
│   └── run_batch.py          # バッチ統合実行
├── database/                 # データベース関連
│   ├── models.py             # テーブル定義
│   ├── database_manager.py   # DB操作クラス
│   └── stock_data.db         # SQLiteファイル
├── config/                   # 設定ファイル
│   └── settings.py           # システム設定
├── utils/                    # ユーティリティ
│   ├── jpx_parser.py         # JPXデータ解析
│   └── market_analyzer.py    # 市場分析
└── frontend/                 # UI関連（今後実装予定）
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

### v1.0.0 (2025-08-21)
- 初回リリース
- 基本的なデータ収集・技術分析・投資候補抽出機能
- バッチ処理システム
- SQLiteデータベース対応