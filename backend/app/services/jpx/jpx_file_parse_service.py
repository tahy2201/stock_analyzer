import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from app.config.settings import DATA_DIR, JPX_FILE_NAME
from app.utils.determine_enterprise import determine_enterprise_status

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s], [%(levelname)s], %(name)s -- %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class JPXFileParseService:
    def __init__(self) -> None:
        self.data_dir = DATA_DIR
        self.jpx_file_path = self.data_dir / JPX_FILE_NAME

    def download_jpx_file(self, url: str = "") -> bool:
        """
        JPXの上場会社一覧ファイルをダウンロード
        Note: 実際のダウンロードは手動で行い、data/フォルダに配置することを想定
        """
        logger.info("JPXファイルは手動でダウンロードしてdata/フォルダに配置してください")
        logger.info(f"配置先: {self.jpx_file_path}")
        logger.info("URL: https://www.jpx.co.jp/markets/statistics-equities/misc/01.html")
        return self.jpx_file_path.exists()

    def parse_jpx_excel(self, file_path: Optional[Path] = None) -> list[dict]:
        """
        JPXのExcelファイルを解析して企業情報を抽出
        """
        if file_path is None:
            file_path = self.jpx_file_path

        if not file_path.exists():
            logger.error(f"JPXファイルが見つかりません: {file_path}")
            return []

        try:
            # Excelファイルの読み込み（複数のエンジンを試行）
            try:
                df = pd.read_excel(file_path, engine="openpyxl")
            except Exception:
                try:
                    df = pd.read_excel(file_path, engine="xlrd")
                except Exception:
                    logger.error(f"Excelファイルの読み込みに失敗: {file_path}")
                    return []

            companies = []

            # JPXファイルの一般的な構造を想定した解析
            # 実際のファイル構造に応じて調整が必要
            for index, row in df.iterrows():
                try:
                    # 基本的な企業情報の抽出
                    company_data = self._extract_company_info(row)
                    if company_data:
                        companies.append(company_data)
                except Exception as e:
                    logger.warning(f"行 {index} の解析に失敗: {e}")
                    continue

            logger.info(f"JPXファイルから {len(companies)} 社の情報を抽出しました")
            return companies

        except Exception as e:
            logger.error(f"JPXファイルの解析に失敗: {e}")
            return []

    def _extract_company_info(self, row: pd.Series) -> Optional[dict]:
        """
        行データから企業情報を抽出
        JPXファイルの実際の構造に応じてカスタマイズが必要
        """
        try:
            # 一般的な列名パターンを想定
            symbol_candidates = ["コード", "Code", "Symbol", "銘柄コード", "証券コード"]
            name_candidates = ["銘柄名", "Name", "会社名", "企業名"]
            sector_candidates = ["業種", "Sector", "33業種区分", "17業種区分"]
            market_candidates = ["市場・商品区分", "Market", "上場区分", "市場区分"]

            symbol = None
            name = None
            sector = None
            market = None

            # シンボル（証券コード）の抽出
            for candidate in symbol_candidates:
                if candidate in row.index and pd.notna(row[candidate]):
                    symbol = str(row[candidate]).strip()
                    # 4桁の数字のみ抽出
                    if symbol.isdigit() and len(symbol) == 4:
                        break
                    # 4桁 + .T の形式から4桁のみ抽出
                    if "." in symbol:
                        symbol = symbol.split(".")[0]
                        if symbol.isdigit() and len(symbol) == 4:
                            break

            # 企業名の抽出
            for candidate in name_candidates:
                if candidate in row.index and pd.notna(row[candidate]):
                    name = str(row[candidate]).strip()
                    break

            # 業種の抽出
            for candidate in sector_candidates:
                if candidate in row.index and pd.notna(row[candidate]):
                    sector = str(row[candidate]).strip()
                    break

            # 市場区分の抽出
            for candidate in market_candidates:
                if candidate in row.index and pd.notna(row[candidate]):
                    market = str(row[candidate]).strip()
                    break

            # 必要最小限の情報があるかチェック
            if not symbol or not name:
                return None

            # エンタープライズ企業の判定（基本的な条件）
            is_enterprise = determine_enterprise_status(name, sector, market)

            return {
                "symbol": symbol,
                "name": name,
                "sector": sector or "Unknown",
                "market": market or "Unknown",
                "employees": None,  # JPXファイルには通常含まれない
                "revenue": None,  # JPXファイルには通常含まれない
                "is_enterprise": is_enterprise,
            }

        except Exception as e:
            logger.warning(f"企業情報抽出エラー: {e}")
            return None
