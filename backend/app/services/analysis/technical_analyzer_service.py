import logging
from typing import Optional

import pandas as pd

from app.config.constants import MARKET_NAME_MAPPING
from app.config.settings import (
    DIVERGENCE_THRESHOLD,
    DIVIDEND_YIELD_MAX,
    DIVIDEND_YIELD_MIN,
    MA_PERIOD,
)
from app.database.database_manager import DatabaseManager
from app.utils.price_indicators import (
    calculate_divergence_rate,
    calculate_moving_average,
    calculate_price_change_percent,
    calculate_volume_average,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s], [%(levelname)s], %(name)s -- %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TechnicalAnalyzerService:
    def __init__(self) -> None:
        self.db_manager = DatabaseManager()

    def get_dividend_yield(
        self, symbol: str, current_price: Optional[float] = None
    ) -> Optional[float]:
        """
        配当利回りを計算（ticker_infoの年間配当金と現在の株価から計算）
        """
        try:
            ticker_info = self.db_manager.get_ticker_info(symbol)

            if not ticker_info:
                logger.debug(f"ticker_infoデータなし: {symbol}")
                return 0.0

            annual_dividend = ticker_info.get("trailing_annual_dividend_rate")
            if annual_dividend is None or annual_dividend <= 0:
                logger.debug(f"年間配当金データなし: {symbol}")
                return 0.0

            # 現在の株価を取得（引数で指定されていない場合は最新の株価データを使用）
            if current_price is None:
                price_data = self.db_manager.get_stock_prices(symbol)
                if price_data.empty:
                    # 株価データがない場合はticker_infoの株価を使用
                    ticker_price = ticker_info.get("current_price")
                    if ticker_price is None or ticker_price <= 0:
                        logger.debug(f"株価データなし: {symbol}")
                        return 0.0
                    current_price = ticker_price
                else:
                    current_price = float(price_data["close"].iloc[-1])

            if current_price is None or current_price <= 0:
                logger.warning(f"無効な株価: {symbol}, price: {current_price}")
                return 0.0

            # 配当利回り計算：(年間配当金 / 現在株価) * 100
            dividend_yield = (float(annual_dividend) / current_price) * 100
            return round(dividend_yield, 2)

        except Exception as e:
            logger.warning(f"配当利回り計算エラー {symbol}: {e}")
            return 0.0

    def analyze_single_stock(self, symbol: str) -> Optional[dict]:
        """
        単一銘柄の技術分析を実行
        """
        try:
            logger.debug(f"技術分析開始: {symbol}")

            # データベースから株価データを取得
            price_data = self.db_manager.get_stock_prices(symbol)
            if price_data.empty:
                logger.warning(f"株価データが見つかりません: {symbol}")
                return None

            # 必要なデータ期間があるかチェック
            if len(price_data) < MA_PERIOD:
                logger.warning(f"データ不足 {symbol}: {len(price_data)} < {MA_PERIOD}")
                return None

            # 技術指標の計算
            close_prices = price_data["close"]
            volumes = price_data["volume"]

            # 25日移動平均
            ma_25 = calculate_moving_average(close_prices, MA_PERIOD)

            # 出来高移動平均
            volume_avg_20 = calculate_volume_average(volumes, 20)

            # 最新の値を取得
            latest_date = price_data.index[-1]
            latest_price = close_prices.iloc[-1]
            latest_ma_25 = ma_25.iloc[-1]
            latest_volume_avg = volume_avg_20.iloc[-1]

            # 配当利回りの取得（現在の株価を使用）
            dividend_yield = self.get_dividend_yield(symbol, latest_price)

            # 結果をDataFrameとして構築
            indicators_df = pd.DataFrame(
                {
                    "ma_25": ma_25,
                    "divergence_rate": [
                        calculate_divergence_rate(price, ma)
                        for price, ma in zip(close_prices, ma_25)
                    ],
                    "dividend_yield": dividend_yield,  # 全期間で同じ値
                    "volume_avg_20": volume_avg_20,
                },
                index=price_data.index,
            )

            # 欠損値を除去
            indicators_df = indicators_df.dropna()

            # 最新の乖離率をDataFrameから取得
            latest_divergence_rate = float(indicators_df["divergence_rate"].iloc[-1])

            # データベースに保存
            success = self.db_manager.insert_technical_indicators(symbol, indicators_df)

            if success:
                logger.debug(f"技術分析完了: {symbol}")
                return {
                    "symbol": symbol,
                    "latest_price": latest_price,
                    "latest_ma_25": latest_ma_25,
                    "divergence_rate": latest_divergence_rate,
                    "dividend_yield": dividend_yield,
                    "latest_volume_avg": latest_volume_avg,
                    "analysis_date": latest_date,
                }
            else:
                logger.error(f"技術指標保存失敗: {symbol}")
                return None

        except Exception as e:
            logger.error(f"技術分析エラー {symbol}: {e}")
            return None

    def analyze_batch_stocks(self, symbols: list[str]) -> dict[str, Optional[dict]]:
        """
        複数銘柄の技術分析をバッチ実行
        """
        results = {}

        logger.info(f"技術分析開始: {len(symbols)} 銘柄")

        for i, symbol in enumerate(symbols):
            if (i + 1) % 50 == 0:
                logger.info(f"進捗: {i + 1}/{len(symbols)}")

            result = self.analyze_single_stock(symbol)
            results[symbol] = result

        success_count = sum(1 for result in results.values() if result is not None)
        logger.info(f"技術分析完了: 成功 {success_count}/{len(symbols)}")

        return results

    def get_investment_candidates(
        self,
        divergence_threshold: float = DIVERGENCE_THRESHOLD,
        dividend_min: float = DIVIDEND_YIELD_MIN,
        dividend_max: float = DIVIDEND_YIELD_MAX,
        market_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        投資候補銘柄を抽出
        """
        try:
            # 市場フィルタを日本語名に変換
            actual_market_filter = None
            if market_filter:
                actual_market_filter = MARKET_NAME_MAPPING.get(market_filter, market_filter)

            # フィルタリング条件でデータベースから抽出
            # divergence_thresholdがマイナス値の場合は、それより低い（より悪い）乖離率を指定
            candidates = self.db_manager.get_filtered_companies(
                divergence_max=divergence_threshold,  # 乖離率の上限（株価が移動平均線より低い場合）
                dividend_yield_min=dividend_min,
                dividend_yield_max=dividend_max,
                is_enterprise_only=True,
                market_filter=actual_market_filter,
            )

            logger.info(f"投資候補銘柄: {len(candidates)} 銘柄が抽出されました")

            # 追加の分析情報を付与
            enriched_candidates = []
            for candidate in candidates:
                try:
                    # 最新の株価データを取得
                    price_data = self.db_manager.get_stock_prices(candidate["symbol"])
                    if not price_data.empty:
                        latest_price = price_data["close"].iloc[-1]
                        price_change_1d = (
                            calculate_price_change_percent(
                                float(price_data["close"].iloc[-1]),
                                float(price_data["close"].iloc[-2]),
                            )
                            if len(price_data) > 1
                            else 0.0
                        )

                        candidate.update(
                            {
                                "current_price": latest_price,
                                "latest_price": latest_price,
                                "price_change_1d": round(price_change_1d, 2),
                                "analysis_score": self._calculate_investment_score(candidate),
                            }
                        )

                    enriched_candidates.append(candidate)

                except Exception as e:
                    logger.warning(f"候補銘柄の詳細取得エラー {candidate.get('symbol')}: {e}")
                    enriched_candidates.append(candidate)

            # スコア順でソート
            enriched_candidates.sort(key=lambda x: x.get("analysis_score", 0), reverse=True)

            return enriched_candidates

        except Exception as e:
            logger.error(f"投資候補抽出エラー: {e}")
            return []

    def _calculate_investment_score(self, candidate: dict) -> float:
        """
        投資魅力度スコアを計算
        """
        score = 0.0

        try:
            # 乖離率スコア（絶対値が大きいほど高スコア）
            divergence_rate_raw = candidate.get("divergence_rate")
            if divergence_rate_raw is not None:
                divergence_rate = abs(divergence_rate_raw)
                if divergence_rate >= 10:
                    score += 5
                elif divergence_rate >= 7:
                    score += 4
                elif divergence_rate >= 5:
                    score += 3
                elif divergence_rate >= 3:
                    score += 2

            # 配当利回りスコア
            dividend_yield = candidate.get("dividend_yield")
            if dividend_yield is not None and dividend_yield > 0:
                if 3.5 <= dividend_yield <= 4.5:
                    score += 3
                elif 3.0 <= dividend_yield <= 5.0:
                    score += 2
                else:
                    score += 1

            # 企業規模スコア
            if candidate.get("is_enterprise"):
                score += 2

            # 市場区分スコア
            market = candidate.get("market", "").lower()
            if "プライム" in market or "prime" in market:
                score += 2
            elif "スタンダード" in market or "standard" in market:
                score += 1

            return round(score, 1)

        except Exception as e:
            logger.warning(f"スコア計算エラー: {e}")
            return 0.0

    def get_technical_summary(self, symbol: str) -> Optional[dict]:
        """
        銘柄の技術分析サマリーを取得
        """
        try:
            # 技術指標データの取得
            indicators = self.db_manager.get_technical_indicators(symbol)
            if indicators.empty:
                return None

            # 株価データの取得
            prices = self.db_manager.get_stock_prices(symbol)
            if prices.empty:
                return None

            latest_indicators = indicators.iloc[-1]
            latest_prices = prices.iloc[-1]

            # トレンド分析
            ma_trend = self._analyze_ma_trend(indicators["ma_25"].tail(5))
            price_trend = self._analyze_price_trend(prices["close"].tail(5))

            return {
                "symbol": symbol,
                "current_price": latest_prices["close"],
                "ma_25": latest_indicators["ma_25"],
                "divergence_rate": latest_indicators["divergence_rate"],
                "dividend_yield": latest_indicators["dividend_yield"],
                "volume_avg_20": latest_indicators["volume_avg_20"],
                "ma_trend": ma_trend,
                "price_trend": price_trend,
                "last_updated": indicators.index[-1],
            }

        except Exception as e:
            logger.error(f"技術分析サマリー取得エラー {symbol}: {e}")
            return None

    def _analyze_ma_trend(self, ma_series: pd.Series) -> str:
        """
        移動平均のトレンド分析
        """
        if len(ma_series) < 2:
            return "Unknown"

        recent_slope = ma_series.iloc[-1] - ma_series.iloc[-2]
        longer_slope = (
            ma_series.iloc[-1] - ma_series.iloc[0] if len(ma_series) >= 5 else recent_slope
        )

        if recent_slope > 0 and longer_slope > 0:
            return "Upward"
        elif recent_slope < 0 and longer_slope < 0:
            return "Downward"
        else:
            return "Sideways"

    def _analyze_price_trend(self, price_series: pd.Series) -> str:
        """
        価格のトレンド分析
        """
        if len(price_series) < 2:
            return "Unknown"

        recent_change = ((price_series.iloc[-1] / price_series.iloc[-2]) - 1) * 100

        if recent_change > 2:
            return "Strong Up"
        elif recent_change > 0:
            return "Up"
        elif recent_change < -2:
            return "Strong Down"
        elif recent_change < 0:
            return "Down"
        else:
            return "Flat"


if __name__ == "__main__":
    analyzer = TechnicalAnalyzerService()

    # テスト用: 特定銘柄の技術分析
    test_symbols = ["7203", "6758", "9984"]

    print("技術分析テストを開始...")
    results = analyzer.analyze_batch_stocks(test_symbols)

    print("\n技術分析結果:")
    for symbol, result in results.items():
        if result:
            print(
                f"  {symbol}: 乖離率 {result['divergence_rate']}%, 配当利回り {result['dividend_yield']}%"
            )
        else:
            print(f"  {symbol}: 分析失敗")

    # 投資候補の抽出テスト
    print("\n投資候補銘柄の抽出...")
    candidates = analyzer.get_investment_candidates()

    print(f"候補銘柄数: {len(candidates)}")
    for candidate in candidates[:5]:  # 上位5銘柄
        print(
            f"  {candidate['symbol']} ({candidate['name']}): "
            f"乖離率 {candidate.get('divergence_rate', 0)}%, "
            f"配当 {candidate.get('dividend_yield', 0)}%, "
            f"スコア {candidate.get('analysis_score', 0)}"
        )
