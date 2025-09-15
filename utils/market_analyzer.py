import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from config.settings import MA_PERIOD, MARKET_INDICES
from database.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketAnalyzer:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.market_indices = MARKET_INDICES

    def get_market_data(self, index_name: str, days: int = 252) -> Optional[pd.DataFrame]:
        """
        市場指数データを取得
        """
        try:
            # データベースから指数データを取得
            index_symbol = f"INDEX_{index_name}"
            data = self.db_manager.get_stock_prices(index_symbol)

            if data.empty:
                logger.warning(f"市場指数データが見つかりません: {index_name}")
                return None

            # 指定日数分のデータを取得
            if len(data) > days:
                data = data.tail(days)

            return data

        except Exception as e:
            logger.error(f"市場指数データ取得エラー {index_name}: {e}")
            return None

    def calculate_market_trend(self, index_data: pd.DataFrame) -> Dict:
        """
        市場トレンドを分析
        """
        try:
            if index_data.empty:
                return {}

            close_prices = index_data["close"]

            # 移動平均の計算
            ma_25 = close_prices.rolling(window=25, min_periods=25).mean()
            ma_75 = close_prices.rolling(window=75, min_periods=75).mean()

            # 現在値と移動平均の関係
            current_price = close_prices.iloc[-1]
            current_ma_25 = ma_25.iloc[-1] if not ma_25.empty else current_price
            current_ma_75 = ma_75.iloc[-1] if not ma_75.empty else current_price

            # トレンド判定
            trend = self._determine_trend(current_price, current_ma_25, current_ma_75)

            # ボラティリティ計算（過去30日）
            returns = close_prices.pct_change().dropna()
            volatility = returns.tail(30).std() * np.sqrt(252) * 100  # 年率換算

            # 価格変化率
            price_changes = {
                "1d": ((close_prices.iloc[-1] / close_prices.iloc[-2]) - 1) * 100
                if len(close_prices) > 1
                else 0,
                "5d": ((close_prices.iloc[-1] / close_prices.iloc[-6]) - 1) * 100
                if len(close_prices) > 5
                else 0,
                "1m": ((close_prices.iloc[-1] / close_prices.iloc[-21]) - 1) * 100
                if len(close_prices) > 21
                else 0,
                "3m": ((close_prices.iloc[-1] / close_prices.iloc[-63]) - 1) * 100
                if len(close_prices) > 63
                else 0,
            }

            return {
                "current_price": current_price,
                "ma_25": current_ma_25,
                "ma_75": current_ma_75,
                "trend": trend,
                "volatility": volatility,
                "price_changes": price_changes,
                "last_updated": index_data.index[-1],
            }

        except Exception as e:
            logger.error(f"市場トレンド分析エラー: {e}")
            return {}

    def _determine_trend(self, current_price: float, ma_25: float, ma_75: float) -> str:
        """
        トレンドを判定
        """
        try:
            if pd.isna(ma_25) or pd.isna(ma_75):
                return "Unknown"

            # 価格と移動平均の位置関係
            above_ma25 = current_price > ma_25
            above_ma75 = current_price > ma_75
            ma25_above_ma75 = ma_25 > ma_75

            # 移動平均からの乖離率
            divergence_25 = ((current_price - ma_25) / ma_25) * 100
            divergence_75 = ((current_price - ma_75) / ma_75) * 100

            # トレンド判定ロジック
            if above_ma25 and above_ma75 and ma25_above_ma75:
                if divergence_25 > 5:
                    return "Strong Uptrend"
                else:
                    return "Uptrend"
            elif not above_ma25 and not above_ma75 and not ma25_above_ma75:
                if divergence_25 < -5:
                    return "Strong Downtrend"
                else:
                    return "Downtrend"
            elif above_ma25 and ma25_above_ma75:
                return "Weak Uptrend"
            elif not above_ma25 and not ma25_above_ma75:
                return "Weak Downtrend"
            else:
                return "Sideways"

        except Exception as e:
            logger.warning(f"トレンド判定エラー: {e}")
            return "Unknown"

    def is_market_overheated(
        self, threshold_days: int = 30, threshold_percentage: float = 15.0
    ) -> Dict:
        """
        市場が高騰状態かどうかを判定
        """
        market_status = {}
        overall_overheated = False
        overheated_count = 0

        for index_name in self.market_indices.keys():
            try:
                index_data = self.get_market_data(index_name)
                if index_data is None or index_data.empty:
                    market_status[index_name] = {
                        "overheated": False,
                        "reason": "データなし",
                        "change_percentage": 0,
                    }
                    continue

                # 指定期間での価格変化を確認
                if len(index_data) < threshold_days:
                    threshold_days = len(index_data) - 1

                if threshold_days <= 0:
                    market_status[index_name] = {
                        "overheated": False,
                        "reason": "データ不足",
                        "change_percentage": 0,
                    }
                    continue

                recent_price = index_data["close"].iloc[-1]
                past_price = index_data["close"].iloc[-(threshold_days + 1)]

                change_percentage = ((recent_price - past_price) / past_price) * 100

                is_overheated = change_percentage > threshold_percentage

                # ボラティリティも考慮
                returns = index_data["close"].pct_change().dropna()
                recent_volatility = returns.tail(threshold_days).std() * 100

                # 高ボラティリティの場合は過熱判定を強化
                if recent_volatility > 2.0 and change_percentage > threshold_percentage * 0.7:
                    is_overheated = True

                market_status[index_name] = {
                    "overheated": is_overheated,
                    "change_percentage": round(change_percentage, 2),
                    "volatility": round(recent_volatility, 2),
                    "reason": f"{threshold_days}日間で{change_percentage:.1f}%変化"
                    if is_overheated
                    else "正常範囲",
                }

                if is_overheated:
                    overheated_count += 1

            except Exception as e:
                logger.error(f"過熱判定エラー {index_name}: {e}")
                market_status[index_name] = {
                    "overheated": False,
                    "reason": f"エラー: {e}",
                    "change_percentage": 0,
                }

        # 全体の過熱判定（過半数が過熱状態の場合）
        overall_overheated = overheated_count > len(self.market_indices) / 2

        return {
            "overall_overheated": overall_overheated,
            "overheated_indices_count": overheated_count,
            "total_indices": len(self.market_indices),
            "indices_status": market_status,
            "analysis_date": datetime.now().isoformat(),
        }

    def get_market_summary(self) -> Dict:
        """
        市場全体のサマリーを取得
        """
        summary = {
            "analysis_date": datetime.now().isoformat(),
            "indices_analysis": {},
            "overall_sentiment": "Unknown",
            "investment_timing": "Unknown",
        }

        trend_scores = []

        for index_name in self.market_indices.keys():
            try:
                index_data = self.get_market_data(index_name)
                if index_data is None or index_data.empty:
                    continue

                trend_analysis = self.calculate_market_trend(index_data)
                summary["indices_analysis"][index_name] = trend_analysis

                # トレンドスコア化
                trend = trend_analysis.get("trend", "Unknown")
                score = self._trend_to_score(trend)
                trend_scores.append(score)

            except Exception as e:
                logger.error(f"市場サマリーエラー {index_name}: {e}")

        # 全体的な市場センチメント
        if trend_scores:
            avg_score = sum(trend_scores) / len(trend_scores)
            summary["overall_sentiment"] = self._score_to_sentiment(avg_score)
            summary["average_trend_score"] = round(avg_score, 2)

        # 過熱状況
        overheated_analysis = self.is_market_overheated()
        summary["overheated_analysis"] = overheated_analysis

        # 投資タイミングの判定
        summary["investment_timing"] = self._determine_investment_timing(
            summary["overall_sentiment"], overheated_analysis["overall_overheated"]
        )

        return summary

    def _trend_to_score(self, trend: str) -> float:
        """
        トレンドをスコアに変換
        """
        score_map = {
            "Strong Uptrend": 2.0,
            "Uptrend": 1.5,
            "Weak Uptrend": 1.0,
            "Sideways": 0.0,
            "Weak Downtrend": -1.0,
            "Downtrend": -1.5,
            "Strong Downtrend": -2.0,
            "Unknown": 0.0,
        }
        return score_map.get(trend, 0.0)

    def _score_to_sentiment(self, score: float) -> str:
        """
        スコアをセンチメントに変換
        """
        if score > 1.5:
            return "Very Bullish"
        elif score > 0.5:
            return "Bullish"
        elif score > -0.5:
            return "Neutral"
        elif score > -1.5:
            return "Bearish"
        else:
            return "Very Bearish"

    def _determine_investment_timing(self, sentiment: str, is_overheated: bool) -> str:
        """
        投資タイミングを判定
        """
        if is_overheated:
            return "Wait"  # 市場過熱時は待機
        elif sentiment in ["Very Bearish", "Bearish"]:
            return "Good"  # 弱気相場は投資好機
        elif sentiment == "Neutral":
            return "Moderate"  # 中立は中程度の投資機会
        elif sentiment in ["Bullish", "Very Bullish"]:
            return "Caution"  # 強気相場は慎重に
        else:
            return "Unknown"

    def get_sector_rotation_analysis(self) -> Dict:
        """
        セクターローテーション分析（簡易版）
        """
        try:
            # データベースから各セクターの企業を取得
            companies = self.db_manager.get_companies(is_enterprise_only=True)

            # セクター別の集計
            sector_performance = {}

            for company in companies:
                sector = company.get("sector", "Unknown")
                if sector not in sector_performance:
                    sector_performance[sector] = {"count": 0, "symbols": []}

                sector_performance[sector]["count"] += 1
                sector_performance[sector]["symbols"].append(company["symbol"])

            # 上位セクターのトレンド分析（実装は簡略化）
            top_sectors = sorted(
                sector_performance.items(), key=lambda x: x[1]["count"], reverse=True
            )[:10]

            return {
                "analysis_date": datetime.now().isoformat(),
                "sector_distribution": dict(top_sectors),
                "total_sectors": len(sector_performance),
                "note": "詳細な株価パフォーマンス分析は将来実装予定",
            }

        except Exception as e:
            logger.error(f"セクターローテーション分析エラー: {e}")
            return {}


if __name__ == "__main__":
    analyzer = MarketAnalyzer()

    print("市場分析テストを開始...")

    # 市場サマリーの取得
    summary = analyzer.get_market_summary()

    print("\n市場サマリー:")
    print(f"  全体センチメント: {summary.get('overall_sentiment')}")
    print(f"  投資タイミング: {summary.get('investment_timing')}")
    print(
        f"  過熱状況: {'過熱' if summary.get('overheated_analysis', {}).get('overall_overheated') else '正常'}"
    )

    print("\n各指数の分析:")
    for index_name, analysis in summary.get("indices_analysis", {}).items():
        print(f"  {index_name}:")
        print(f"    トレンド: {analysis.get('trend')}")
        print(f"    現在値: {analysis.get('current_price', 0):.2f}")
        print(f"    ボラティリティ: {analysis.get('volatility', 0):.2f}%")

    # 過熱分析の詳細
    overheated = analyzer.is_market_overheated()
    print(f"\n過熱分析:")
    print(f"  過熱指数数: {overheated['overheated_indices_count']}/{overheated['total_indices']}")
    for index_name, status in overheated["indices_status"].items():
        status_text = "過熱" if status["overheated"] else "正常"
        print(f"  {index_name}: {status_text} ({status['change_percentage']}%)")

    # セクター分析
    sector_analysis = analyzer.get_sector_rotation_analysis()
    print(f"\nセクター分析:")
    print(f"  総セクター数: {sector_analysis.get('total_sectors', 0)}")

    sector_dist = sector_analysis.get("sector_distribution", {})
    print("  上位セクター:")
    for sector, data in list(sector_dist.items())[:5]:
        print(f"    {sector}: {data['count']} 社")
