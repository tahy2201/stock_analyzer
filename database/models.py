import sqlite3
from pathlib import Path

from config.settings import DATABASE_PATH


def create_tables():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            symbol VARCHAR(10) PRIMARY KEY,
            name VARCHAR(255),
            sector VARCHAR(100),
            market VARCHAR(50),
            employees INTEGER,
            revenue BIGINT,
            is_enterprise BOOLEAN,
            dividend_yield DECIMAL(5,2),
            last_updated DATETIME
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            symbol VARCHAR(10),
            date DATE,
            open DECIMAL(10,2),
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            close DECIMAL(10,2),
            volume BIGINT,
            PRIMARY KEY (symbol, date),
            FOREIGN KEY (symbol) REFERENCES companies(symbol)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technical_indicators (
            symbol VARCHAR(10),
            date DATE,
            ma_25 DECIMAL(10,2),
            divergence_rate DECIMAL(5,2),
            dividend_yield DECIMAL(5,2),
            volume_avg_20 BIGINT,
            PRIMARY KEY (symbol, date),
            FOREIGN KEY (symbol) REFERENCES companies(symbol)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date 
        ON stock_prices(symbol, date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_date 
        ON technical_indicators(symbol, date)
    """)

    # 既存のcompaniesテーブルにdividend_yield列を追加（存在しない場合）
    try:
        cursor.execute("ALTER TABLE companies ADD COLUMN dividend_yield DECIMAL(5,2)")
    except sqlite3.OperationalError:
        # 列が既に存在する場合はスキップ
        pass

    conn.commit()
    conn.close()


if __name__ == "__main__":
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    create_tables()
    print(f"Database tables created successfully at {DATABASE_PATH}")
