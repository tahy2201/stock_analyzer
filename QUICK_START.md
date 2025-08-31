# 🚀 クイックスタートガイド

## 日本株投資候補の自動抽出システム

### ステップ1: 環境準備
```bash
# 依存関係のインストール
uv sync

# データベース初期化
uv run python -c "from database.models import create_tables; create_tables()"
```

### ステップ2: JPX上場企業データの取得
1. **JPXサイトからExcelファイルをダウンロード**
   - URL: https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
   - 「上場会社一覧」のExcelファイル（data_j.xls）をダウンロード
   - `data/` フォルダに `data_j.xls` として保存

```bash
# dataディレクトリを作成
mkdir -p data

# ダウンロードしたファイルをコピー（例）
# cp ~/Downloads/data_j.xls data/
```

### ステップ3: 企業データの登録・解析
```bash
# JPXファイルを解析して企業データをデータベースに登録
uv run python utils/jpx_parser.py
```

### ステップ4: 全企業の株価データ収集
```bash
# 全エンタープライズ企業の株価データを収集（20-40分程度）
uv run stock-analyzer --mode data-only
```

### ステップ5: 技術分析実行
```bash
# 全企業の技術分析を実行（移動平均、乖離率、配当利回り計算）
uv run stock-analyzer --mode analysis-only
```

### ステップ6: 投資候補の抽出
```bash
# 条件を満たす投資候補を抽出
uv run python -c "
from batch.technical_analyzer import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()

print('=== 投資候補銘柄抽出 ===')
candidates = analyzer.get_investment_candidates()

print(f'抽出された候補数: {len(candidates)} 銘柄\\n')

if candidates:
    print('上位10銘柄:')
    for i, candidate in enumerate(candidates[:10]):
        print(f'{i+1:2d}. {candidate[\"symbol\"]} ({candidate[\"name\"][:15]})')
        print(f'    乖離率: {candidate.get(\"divergence_rate\", 0):+6.1f}%')
        print(f'    配当率: {candidate.get(\"dividend_yield\", 0):6.1f}%')
        print(f'    スコア: {candidate.get(\"analysis_score\", 0):6.1f}')
        print(f'    業種  : {candidate.get(\"sector\", \"不明\")}')
        print()
else:
    print('条件を満たす銘柄が見つかりませんでした。')
    print('設定を緩くすることを検討してください。')
"
```

### ステップ7: 市場状況の確認
```bash
# 市場全体の状況を確認
uv run python -c "
from utils.market_analyzer import MarketAnalyzer
analyzer = MarketAnalyzer()

print('=== 市場分析 ===')
summary = analyzer.get_market_summary()
overheated = analyzer.is_market_overheated()

print(f'市場センチメント: {summary.get(\"overall_sentiment\", \"不明\")}')
print(f'投資タイミング　: {summary.get(\"investment_timing\", \"不明\")}')
print(f'市場過熱状況　　: {\"過熱\" if overheated.get(\"overall_overheated\") else \"正常\"}')

if overheated.get('overall_overheated'):
    print('\\n⚠️  市場が過熱状態です。投資には慎重になることをお勧めします。')
elif summary.get('investment_timing') == 'Good':
    print('\\n✅ 投資に適したタイミングです。')
"
```

## 🔄 日次更新フロー

一度セットアップが完了すれば、日次更新は簡単です：

```bash
# 日次更新（株価データ更新 → 技術分析 → 投資候補抽出）
uv run stock-analyzer --mode daily
```

### 自動化設定
```bash
# crontabで平日9時に自動実行
# 0 9 * * 1-5 cd /path/to/stock_analyzer && uv run stock-analyzer --mode daily
```

---

## 🔧 オプション機能

### 特定銘柄のみ分析
```bash
# 特定銘柄のみ分析（テスト用）
uv run stock-analyzer --mode daily --symbols 7203,6758,9984
```

### テスト用サンプルデータ
JPXファイルがない場合のテスト用：
```bash
uv run python -c "
from database.database_manager import DatabaseManager
test_companies = [
    {'symbol': '7203', 'name': 'トヨタ自動車', 'sector': 'Transportation', 'market': 'プライム', 'is_enterprise': True},
    {'symbol': '6758', 'name': 'ソニーグループ', 'sector': 'Technology', 'market': 'プライム', 'is_enterprise': True},
    {'symbol': '9984', 'name': 'ソフトバンクグループ', 'sector': 'Technology', 'market': 'プライム', 'is_enterprise': True}
]
db = DatabaseManager()
for company in test_companies:
    success = db.insert_company(company)
    print(f'{company[\"symbol\"]} ({company[\"name\"]}): {\"登録成功\" if success else \"登録失敗\"}')
"

# テストデータで分析実行
uv run stock-analyzer --mode daily --symbols 7203,6758,9984
```

### 分析条件のカスタマイズ
`config/settings.py` を編集：
```python
# より厳しい条件
DIVERGENCE_THRESHOLD = 7.0        # 乖離率7%以上
DIVIDEND_YIELD_MIN = 4.0          # 配当利回り4%以上

# より緩い条件  
DIVERGENCE_THRESHOLD = 3.0        # 乖離率3%以上
DIVIDEND_YIELD_MIN = 2.0          # 配当利回り2%以上
```

---

## 🚨 トラブルシューティング

### エラー1: JPXファイルが見つからない
```bash
# ファイルの配置を確認
ls -la data/data_j.xls

# ファイルが存在しない場合は再ダウンロード
# https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
```

### エラー2: 投資候補が0件
```bash
# より緩い条件で再検索
uv run python -c "
from batch.technical_analyzer import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()
candidates = analyzer.get_investment_candidates(
    divergence_threshold=1.0,  # 1%以上の乖離
    dividend_min=1.0,          # 配当1%以上
    dividend_max=10.0          # 配当10%以下
)
print(f'緩い条件での候補数: {len(candidates)}')
"
```

### エラー3: yfinanceでデータ取得失敗
```bash
# 時間を置いて再実行
sleep 30
uv run stock-analyzer --mode data-only --enterprise-only
```

### エラー4: データベースエラー
```bash
# データベースを再作成
rm database/stock_data.db
uv run python -c "from database.models import create_tables; create_tables()"
```

---

## 📊 システムの動作確認

すべて正常に動作しているかテスト：
```bash
uv run python -c "
import sys
sys.path.append('.')

print('=== システム統合テスト ===')
try:
    from database.database_manager import DatabaseManager
    from batch.technical_analyzer import TechnicalAnalyzer
    from utils.market_analyzer import MarketAnalyzer
    
    db = DatabaseManager()
    stats = db.get_database_stats()
    
    print(f'✓ データベース接続OK')
    print(f'  企業数: {stats.get(\"companies_count\", 0)}')
    print(f'  株価データ有り: {stats.get(\"symbols_with_prices\", 0)}')
    print(f'  技術指標有り: {stats.get(\"symbols_with_indicators\", 0)}')
    
    analyzer = TechnicalAnalyzer()
    candidates = analyzer.get_investment_candidates()
    print(f'✓ 投資候補抽出: {len(candidates)} 銘柄')
    
    market = MarketAnalyzer()
    summary = market.get_market_summary()
    print(f'✓ 市場分析OK: {summary.get(\"overall_sentiment\", \"不明\")}')
    
    print('\\n🎉 システムが正常に動作しています！')
    
except Exception as e:
    print(f'❌ エラー: {e}')
    print('依存関係のインストールを確認してください')
"
```

## 🎯 期待される結果

正常に動作すると：
1. **数百〜数千の上場企業**がデータベースに登録
2. **エンタープライズ企業**（大中規模企業）の株価データが収集
3. **25日移動平均からの乖離**と**配当利回り**で絞り込み
4. **投資候補銘柄**が優先度順でリストアップ
5. **市場全体の状況**も把握可能

これで日本株市場から効率的に投資候補を見つけることができますわ！