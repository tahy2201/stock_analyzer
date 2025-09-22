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

### 🚀 バッチ処理（推奨）

新しいbackend構造を使用したバッチ処理システムです。

#### 基本コマンド
```bash
# プロジェクトルートディレクトリで実行
cd stock_analyzer

# 特定銘柄のみ処理（高速テスト用）
python backend/run_batch.py --symbols 7203

# プライム市場のエンタープライズ企業のみ
python backend/run_batch.py --markets prime --enterprise-only

# 日次更新（推奨）
python backend/run_batch.py --mode daily

# 完全更新（初回またはデータリセット時）
python backend/run_batch.py --mode full
```

#### オプション
```bash
# 複数銘柄指定
python backend/run_batch.py --symbols 7203,6758,9984

# 市場区分指定
python backend/run_batch.py --markets prime,standard,growth

# JPXデータ更新をスキップ
python backend/run_batch.py --symbols 7203 --skip-jpx

# エンタープライズ企業のみ処理
python backend/run_batch.py --enterprise-only
```

#### ヘルプ
```bash
python backend/run_batch.py --help
```

### 🎯 投資候補の抽出
```bash
# 投資候補抽出
python -c "
from backend.services.analysis.technical_analyzer import TechnicalAnalysisService
analyzer = TechnicalAnalysisService()
candidates = analyzer.get_investment_candidates()
for i, candidate in enumerate(candidates[:5]):
    print(f'{i+1}. {candidate[\"symbol\"]} ({candidate[\"name\"]}): 乖離率{candidate.get(\"divergence_rate\", 0):+.1f}%, 配当{candidate.get(\"dividend_yield\", 0):.1f}%')
"
```

### 🔧 個別サービスの使用

#### 技術分析サービス
```python
from backend.services.analysis.technical_analyzer import TechnicalAnalysisService
analyzer = TechnicalAnalysisService()

# 特定銘柄の技術分析
result = analyzer.analyze_single_stock('7203')

# 投資候補抽出
candidates = analyzer.get_investment_candidates(
    divergence_threshold=5.0,
    dividend_min=3.0,
    dividend_max=5.0
)
```

#### データ収集サービス
```python
from backend.services.data.stock_data_service import StockDataService
data_service = StockDataService()

# 株価データ収集
results = data_service.collect_stock_prices(['7203', '6758'])

# ティッカー情報収集
results = data_service.collect_ticker_info(['7203', '6758'])
```

## ⚙️ 設定

### backend/shared/config/settings.py での設定変更

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
uv run python -c "from backend.shared.database.models import create_tables; create_tables()"
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