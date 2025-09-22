import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { analysisApi, candidatesApi } from '../services/api'
import type { SystemStats, CandidatesCount } from '../types/stock'

const Dashboard = () => {
  // システム統計取得
  const { data: systemStats, isLoading: statsLoading } = useQuery<SystemStats>({
    queryKey: ['systemStats'],
    queryFn: analysisApi.getSystemStats,
  })

  // 投資候補統計取得
  const { data: candidatesCount, isLoading: candidatesLoading } = useQuery<CandidatesCount>({
    queryKey: ['candidatesCount'],
    queryFn: candidatesApi.getCandidatesCount,
  })

  if (statsLoading || candidatesLoading) {
    return (
      <div className="dashboard">
        <h1>📊 ダッシュボード</h1>
        <div>読み込み中...</div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <h1>📊 ダッシュボード</h1>

      <div className="stats-grid">
        {/* システム統計 */}
        <div className="stat-card">
          <h3>🏢 企業データ</h3>
          <div className="stat-value">{systemStats?.companies_count || 0}</div>
          <div className="stat-label">登録企業数</div>
        </div>

        <div className="stat-card">
          <h3>📈 株価データ</h3>
          <div className="stat-value">{systemStats?.symbols_with_prices || 0}</div>
          <div className="stat-label">株価データ有り</div>
        </div>

        <div className="stat-card">
          <h3>🔍 技術分析</h3>
          <div className="stat-value">{systemStats?.symbols_with_technical || 0}</div>
          <div className="stat-label">分析済み銘柄</div>
        </div>

        {/* 投資候補統計 */}
        <div className="stat-card">
          <h3>🎯 投資候補</h3>
          <div className="stat-value">{candidatesCount?.total_candidates || 0}</div>
          <div className="stat-label">候補銘柄数</div>
        </div>

        <div className="stat-card">
          <h3>⭐ 高スコア</h3>
          <div className="stat-value">{candidatesCount?.high_score || 0}</div>
          <div className="stat-label">スコア5以上</div>
        </div>

        <div className="stat-card">
          <h3>📅 最新更新</h3>
          <div className="stat-value">
            {systemStats?.latest_price_date ?
              new Date(systemStats.latest_price_date).toLocaleDateString('ja-JP') :
              '未更新'
            }
          </div>
          <div className="stat-label">株価データ</div>
        </div>
      </div>

      {/* クイックアクション */}
      <div className="quick-actions">
        <h2>🚀 クイックアクション</h2>
        <div className="action-grid">
          <Link to="/candidates" className="action-card">
            <h3>🎯 投資候補を見る</h3>
            <p>AI分析による投資候補銘柄をチェック</p>
          </Link>

          <Link to="/stocks" className="action-card">
            <h3>📊 銘柄検索</h3>
            <p>個別銘柄の詳細情報を確認</p>
          </Link>

          <Link to="/analysis" className="action-card">
            <h3>📈 市場分析</h3>
            <p>技術分析とトレンドを分析</p>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard