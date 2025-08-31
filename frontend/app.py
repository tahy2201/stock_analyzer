import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from database.database_manager import DatabaseManager
from config.settings import DATABASE_PATH

# ページ設定
st.set_page_config(
    page_title="株式分析システム",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# データベース接続
@st.cache_resource
def get_db_connection():
    return DatabaseManager()

# データ取得関数
@st.cache_data(ttl=300)  # 5分キャッシュ
def get_investment_candidates(limit=None):
    """投資候補を取得"""
    db = get_db_connection()
    conn = db.get_connection()
    
    query = '''
    SELECT 
        c.symbol, c.name, c.sector, c.market,
        ti.divergence_rate, ti.dividend_yield, ti.ma_25,
        sp.close as latest_price, sp.date as latest_date,
        (CASE 
            WHEN ti.divergence_rate < -10 AND ti.dividend_yield > 2.0 THEN 100
            WHEN ti.divergence_rate < -5 AND ti.dividend_yield > 1.5 THEN 80
            WHEN ti.divergence_rate < -3 AND ti.dividend_yield > 1.0 THEN 60
            ELSE 0
        END) as score
    FROM technical_indicators ti
    JOIN companies c ON ti.symbol = c.symbol
    LEFT JOIN (
        SELECT symbol, close, date,
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) as rn
        FROM stock_prices
    ) sp ON ti.symbol = sp.symbol AND sp.rn = 1
    WHERE ti.divergence_rate IS NOT NULL 
        AND ti.dividend_yield IS NOT NULL
        AND ti.divergence_rate < 0
        AND c.is_enterprise = 1
        AND ti.date = (SELECT MAX(date) FROM technical_indicators WHERE symbol = ti.symbol)
    ORDER BY score DESC, ti.divergence_rate ASC
    '''
    
    if limit:
        query += f' LIMIT {limit}'
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def get_latest_stock_price(symbol):
    """最新株価を取得"""
    db = get_db_connection()
    conn = db.get_connection()
    
    query = '''
    SELECT close, date, volume
    FROM stock_prices 
    WHERE symbol = ?
    ORDER BY date DESC
    LIMIT 1
    '''
    
    result = conn.execute(query, (symbol,)).fetchone()
    conn.close()
    
    return result

@st.cache_data(ttl=300)
def get_stock_price_data(symbol, days=90):
    """株価データを取得"""
    db = get_db_connection()
    conn = db.get_connection()
    
    query = '''
    SELECT date, open, high, low, close, volume
    FROM stock_prices 
    WHERE symbol = ?
    ORDER BY date DESC
    LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=(symbol, days))
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    
    return df

@st.cache_data(ttl=300)
def get_database_stats():
    """データベース統計を取得"""
    db = get_db_connection()
    return db.get_database_stats()

# メインアプリケーション
def main():
    # サイドバー
    st.sidebar.title("📊 株式分析システム")
    
    # URLパラメーターを最初に処理
    query_params = st.query_params
    url_page = query_params.get('page', None)
    url_symbol = query_params.get('symbol', None)
    
    # セッション状態の初期化
    if 'page' not in st.session_state:
        st.session_state['page'] = url_page if url_page else 'dashboard'
    if 'selected_symbol' not in st.session_state:
        st.session_state['selected_symbol'] = url_symbol if url_symbol else ''
    
    # URLパラメーターがある場合はセッション状態を更新
    if url_page and url_page != st.session_state.get('page'):
        st.session_state['page'] = url_page
    if url_symbol and url_symbol != st.session_state.get('selected_symbol'):
        st.session_state['selected_symbol'] = url_symbol
    
    # ページ選択
    pages = {
        "🏠 ダッシュボード": "dashboard",
        "📋 投資候補一覧": "candidates",
        "🔍 個別銘柄分析": "analysis",
        "📈 システム統計": "stats"
    }
    
    # セッション状態に基づいてページを決定
    if st.session_state.get('page') in pages.values():
        page = st.session_state['page']
        # ラジオボタンのインデックスを設定
        page_keys = list(pages.keys())
        page_values = list(pages.values())
        current_index = page_values.index(page) if page in page_values else 0
    else:
        current_index = 0
        page = "dashboard"
    
    selected_page = st.sidebar.radio("ページを選択", list(pages.keys()), index=current_index)
    
    # ラジオボタンで選択された場合はセッション状態とURLを更新
    if pages[selected_page] != st.session_state.get('page'):
        st.session_state['page'] = pages[selected_page]
        # URLパラメーターも更新
        st.query_params.page = pages[selected_page]
        st.rerun()
    
    page = st.session_state['page']
    
    # メインコンテンツ
    if page == "dashboard":
        show_dashboard()
    elif page == "candidates":
        show_candidates()
    elif page == "analysis":
        show_analysis()
    elif page == "stats":
        show_stats()

def show_dashboard():
    """ダッシュボード表示"""
    st.title("📊 株式投資ダッシュボード")
    
    # 統計情報
    stats = get_database_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", f"{stats.get('companies_count', 0):,}")
    
    with col2:
        st.metric("株価データ有り", f"{stats.get('symbols_with_prices', 0):,}")
    
    with col3:
        st.metric("技術分析完了", f"{stats.get('symbols_with_indicators', 0):,}")
    
    with col4:
        success_rate = (stats.get('symbols_with_prices', 0) / max(stats.get('companies_count', 1), 1)) * 100
        st.metric("データ取得率", f"{success_rate:.1f}%")
    
    st.divider()
    
    # トップ投資候補
    st.subheader("🎯 注目投資候補 TOP 10")
    
    candidates = get_investment_candidates(limit=10)
    
    if not candidates.empty:
        # 表示用にデータを整形
        display_df = candidates[['symbol', 'name', 'sector', 'latest_price', 'divergence_rate', 'dividend_yield', 'score']].copy()
        display_df.columns = ['銘柄コード', '会社名', 'セクター', '現在価格(円)', '乖離率(%)', '配当利回り(%)', 'スコア']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("投資候補データがありません")

def show_candidates():
    """投資候補一覧表示"""
    
    # 固定ヘッダー用CSS
    st.markdown("""
    <style>
    .element-container:has(.fixed-header) {
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
        background: var(--background-color) !important;
        padding: 1rem 0 !important;
        border-bottom: 1px solid #ddd !important;
        margin-bottom: 1rem !important;
    }
    .fixed-header {
        background: inherit;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 固定ヘッダーコンテナ
    with st.container():
        st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
        st.title("📋 投資候補一覧")
        
        # フィルタリングオプション
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_score = st.slider("最小スコア", 0, 100, 0)
        
        with col2:
            max_divergence = st.slider("最大乖離率(%)", -50, 0, -3)
        
        with col3:
            min_dividend = st.slider("最小配当利回り(%)", 0.0, 10.0, 3.0)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # データ取得
    candidates = get_investment_candidates()
    
    if not candidates.empty:
        # フィルタリング
        filtered = candidates[
            (candidates['score'] >= min_score) &
            (candidates['divergence_rate'] >= max_divergence) &
            (candidates['dividend_yield'] >= min_dividend)
        ]
        
        st.subheader(f"🎯 投資候補 ({len(filtered)}銘柄)")
        
        if not filtered.empty:
            # CSS for compact table styling
            st.markdown("""
            <style>
            /* フィルターエリア固定 */
            div[data-testid="stContainer"] > div:first-child {
                position: sticky;
                top: 0;
                z-index: 999;
                background: var(--background-color);
                padding: 1rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            /* テーブルヘッダー固定 */
            .table-header-sticky {
                position: sticky;
                top: 160px;
                z-index: 100;
                background: var(--background-color);
                padding: 0.5rem 0;
                border-bottom: 2px solid #ddd;
                margin-bottom: 0.2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            /* ボタンスタイル - 縦中央揃え */
            .stButton > button {
                height: 32px !important;
                padding: 4px 8px !important;
                margin: 0 !important;
                font-size: 12px !important;
                border-radius: 3px !important;
                border: 1px solid #ddd !important;
                background: #f8f9fa !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-width: 60px !important;
                line-height: 1 !important;
            }
            .stButton > button:hover {
                background: #e9ecef !important;
                border-color: #adb5bd !important;
            }
            
            /* 行の高さ統一 */
            .row-container {
                min-height: 24px;
                display: flex;
                align-items: center;
                margin: 0px;
                padding: 0px;
                line-height: 1;
            }
            
            /* テキストの縦中央揃え */
            .cell-text {
                font-size: 13px;
                margin: 0;
                padding: 2px 0;
                line-height: 20px;
                height: 24px;
                display: flex;
                align-items: center;
            }
            
            /* リンクボタンスタイル */
            .symbol-link {
                display: inline-block;
                height: 24px;
                padding: 1px 8px;
                margin: 0;
                font-size: 12px;
                border-radius: 3px;
                border: 1px solid #333;
                background: #333;
                text-decoration: none;
                color: #fff;
                min-width: 60px;
                text-align: center;
                line-height: 20px;
                cursor: pointer;
                font-weight: bold;
            }
            .symbol-link:hover {
                background: #555;
                border-color: #555;
                text-decoration: none;
                color: #fff;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # ヘッダー行（固定）
            st.markdown('<div class="table-header-sticky">', unsafe_allow_html=True)
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([1.2, 2.5, 1.3, 1.2, 1, 1.2, 1.2, 0.8])
            
            with header_col1:
                st.markdown("**銘柄コード**")
            with header_col2:
                st.markdown("**会社名**")
            with header_col3:
                st.markdown("**セクター**")
            with header_col4:
                st.markdown("**現在価格**")
            with header_col5:
                st.markdown("**乖離率**")
            with header_col6:
                st.markdown("**配当利回り**")
            with header_col7:
                st.markdown("**25日線**")
            with header_col8:
                st.markdown("**スコア**")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # データ行（コンパクト表示）
            for idx, row in filtered.iterrows():
                st.markdown('<div class="row-container">', unsafe_allow_html=True)
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.2, 2.5, 1.3, 1.2, 1, 1.2, 1.2, 0.8])
                
                with col1:
                    # 銘柄コード - 別タブ対応のリンク
                    analysis_url = f"http://localhost:8501/?page=analysis&symbol={row['symbol']}"
                    st.markdown(f"""
                    <a href="{analysis_url}" target="_blank" class="symbol-link" title="個別分析を別タブで開く">
                        {row['symbol']}
                    </a>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f'<div class="cell-text">{row["name"]}</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f'<div class="cell-text">{row["sector"] if pd.notna(row["sector"]) else "N/A"}</div>', unsafe_allow_html=True)
                
                with col4:
                    if pd.notna(row['latest_price']):
                        st.markdown(f'<div class="cell-text">{row["latest_price"]:.0f}円</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="cell-text">N/A</div>', unsafe_allow_html=True)
                
                with col5:
                    div_color = "🔴" if row['divergence_rate'] < -5 else "🟡" if row['divergence_rate'] < -1 else "🟢"
                    st.markdown(f'<div class="cell-text">{div_color} {row["divergence_rate"]:.1f}%</div>', unsafe_allow_html=True)
                
                with col6:
                    div_yield_color = "🟢" if row['dividend_yield'] > 5 else "🟡" if row['dividend_yield'] > 2 else "⚪"
                    st.markdown(f'<div class="cell-text">{div_yield_color} {row["dividend_yield"]:.1f}%</div>', unsafe_allow_html=True)
                
                with col7:
                    if pd.notna(row['ma_25']):
                        st.markdown(f'<div class="cell-text">{row["ma_25"]:.0f}円</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="cell-text">N/A</div>', unsafe_allow_html=True)
                
                with col8:
                    score_color = "🔥" if row['score'] >= 100 else "⭐" if row['score'] >= 80 else "✨" if row['score'] >= 60 else "・"
                    st.markdown(f'<div class="cell-text">{score_color} {row["score"]}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # チャート表示
            st.subheader("📊 分布チャート")
            
            fig = px.scatter(
                filtered,
                x='divergence_rate',
                y='dividend_yield',
                size='score',
                color='sector',
                hover_data=['symbol', 'name'],
                title='乖離率 vs 配当利回り',
                labels={
                    'divergence_rate': '乖離率(%)',
                    'dividend_yield': '配当利回り(%)',
                    'sector': 'セクター'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("フィルタ条件に合致する銘柄がありません")
    else:
        st.info("投資候補データがありません")

def show_analysis():
    """個別銘柄分析表示"""
    st.title("🔍 個別銘柄分析")
    
    # 銘柄選択（セッション状態から初期値を設定）
    default_symbol = st.session_state.get('selected_symbol', '6758')
    symbol = st.text_input("銘柄コード (例: 6758)", value=default_symbol)
    
    if symbol:
        # 基本情報取得
        db = get_db_connection()
        conn = db.get_connection()
        
        company_info = conn.execute(
            "SELECT * FROM companies WHERE symbol = ?", (symbol,)
        ).fetchone()
        
        if company_info:
            st.subheader(f"📊 {company_info[1]} ({company_info[0]})")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**セクター**: {company_info[2] or 'N/A'}")
                st.write(f"**市場**: {company_info[3] or 'N/A'}")
                st.write(f"**従業員数**: {company_info[4]:,}人" if company_info[4] else "N/A")
            
            with col2:
                st.write(f"**売上**: {company_info[5]:,}円" if company_info[5] else "N/A")
                st.write(f"**エンタープライズ**: {'Yes' if company_info[6] else 'No'}")
            
            # 技術指標
            tech_data = conn.execute('''
                SELECT divergence_rate, dividend_yield, ma_25, date
                FROM technical_indicators 
                WHERE symbol = ?
                ORDER BY date DESC LIMIT 1
            ''', (symbol,)).fetchone()
            
            if tech_data:
                st.subheader("📈 技術指標")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("乖離率", f"{tech_data[0]:.1f}%")
                with col2:
                    st.metric("配当利回り", f"{tech_data[1]:.1f}%")
                with col3:
                    st.metric("25日移動平均", f"{tech_data[2]:.0f}円")
            
            # 株価チャート
            st.subheader("📊 株価チャート")
            
            price_data = get_stock_price_data(symbol, days=90)
            
            if not price_data.empty:
                # 土日祝日を除外（取引量が0の日を除外）
                trading_data = price_data[price_data['volume'] > 0].copy()
                
                if not trading_data.empty:
                    # 日付を文字列フォーマット（日付のみ）に変換
                    trading_data['date_str'] = pd.to_datetime(trading_data['date']).dt.strftime('%Y-%m-%d')
                    
                    fig = go.Figure(data=go.Candlestick(
                        x=trading_data['date_str'],
                        open=trading_data['open'],
                        high=trading_data['high'],
                        low=trading_data['low'],
                        close=trading_data['close'],
                        name=f"{symbol} 株価"
                    ))
                    
                    # 25日移動平均線も表示
                    if tech_data and tech_data[2]:
                        fig.add_hline(
                            y=tech_data[2], 
                            line_dash="dash", 
                            line_color="red",
                            annotation_text="25日移動平均"
                        )
                    
                    # X軸の設定（土日祝日のギャップを除去、日付のみ表示）
                    fig.update_layout(
                        title=f"{symbol} 株価チャート (過去90営業日)",
                        xaxis_title="日付",
                        yaxis_title="価格(円)",
                        xaxis_rangeslider_visible=False,
                        xaxis=dict(
                            type='category',  # カテゴリ型にして連続表示
                            tickangle=-45,
                            dtick=5  # 5日おきに表示
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("取引データがありません")
            else:
                st.warning("株価データが見つかりません")
        
        conn.close()

def show_stats():
    """システム統計表示"""
    st.title("📈 システム統計")
    
    stats = get_database_stats()
    
    # 基本統計
    st.subheader("📊 データベース統計")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("総企業数", f"{stats.get('companies_count', 0):,}")
        st.metric("株価データ有り", f"{stats.get('symbols_with_prices', 0):,}")
        
    with col2:
        st.metric("技術分析完了", f"{stats.get('symbols_with_indicators', 0):,}")
        success_rate = (stats.get('symbols_with_prices', 0) / max(stats.get('companies_count', 1), 1)) * 100
        st.metric("データ取得成功率", f"{success_rate:.1f}%")
    
    # 投資候補統計
    st.subheader("🎯 投資候補統計")
    
    candidates = get_investment_candidates()
    
    if not candidates.empty:
        # スコア分布
        score_dist = candidates.groupby('score').size().reset_index(name='count')
        
        fig = px.bar(
            score_dist,
            x='score',
            y='count',
            title='投資候補スコア分布',
            labels={'score': 'スコア', 'count': '銘柄数'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # セクター分布
        if 'sector' in candidates.columns:
            sector_dist = candidates['sector'].value_counts().head(10)
            
            fig2 = px.pie(
                values=sector_dist.values,
                names=sector_dist.index,
                title='投資候補セクター分布 (TOP 10)'
            )
            
            st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()