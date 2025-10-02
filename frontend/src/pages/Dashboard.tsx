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
      <div className="max-w-6xl mx-auto p-6">
        <h1 className="text-3xl font-bold text-gray-100 mb-6">📊 ダッシュボード</h1>
        <div className="text-gray-400">読み込み中...</div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-8">📊 ダッシュボード</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {/* システム統計 */}
        <div className="bg-gray-800 p-6 rounded-lg text-center border border-gray-700 hover:border-gray-600 transition-colors">
          <h3 className="text-sm font-medium text-gray-400 mb-4">🏢 企業データ</h3>
          <div className="text-4xl font-bold text-gray-100 mb-2">{systemStats?.companies_count || 0}</div>
          <div className="text-sm text-gray-400">登録企業数</div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg text-center border border-gray-700 hover:border-gray-600 transition-colors">
          <h3 className="text-sm font-medium text-gray-400 mb-4">📈 株価データ</h3>
          <div className="text-4xl font-bold text-gray-100 mb-2">{systemStats?.symbols_with_prices || 0}</div>
          <div className="text-sm text-gray-400">株価データ有り</div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg text-center border border-gray-700 hover:border-gray-600 transition-colors">
          <h3 className="text-sm font-medium text-gray-400 mb-4">🔍 技術分析</h3>
          <div className="text-4xl font-bold text-gray-100 mb-2">{systemStats?.symbols_with_technical || 0}</div>
          <div className="text-sm text-gray-400">分析済み銘柄</div>
        </div>

        {/* 投資候補統計 */}
        <div className="bg-gray-800 p-6 rounded-lg text-center border border-gray-700 hover:border-gray-600 transition-colors">
          <h3 className="text-sm font-medium text-gray-400 mb-4">🎯 投資候補</h3>
          <div className="text-4xl font-bold text-gray-100 mb-2">{candidatesCount?.total_candidates || 0}</div>
          <div className="text-sm text-gray-400">候補銘柄数</div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg text-center border border-gray-700 hover:border-gray-600 transition-colors">
          <h3 className="text-sm font-medium text-gray-400 mb-4">⭐ 高スコア</h3>
          <div className="text-4xl font-bold text-gray-100 mb-2">{candidatesCount?.high_score || 0}</div>
          <div className="text-sm text-gray-400">スコア5以上</div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg text-center border border-gray-700 hover:border-gray-600 transition-colors">
          <h3 className="text-sm font-medium text-gray-400 mb-4">📅 最新更新</h3>
          <div className="text-xl font-bold text-gray-100 mb-2">
            {systemStats?.latest_price_date ?
              new Date(systemStats.latest_price_date).toLocaleDateString('ja-JP') :
              '未更新'
            }
          </div>
          <div className="text-sm text-gray-400">株価データ</div>
        </div>
      </div>

      {/* クイックアクション */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-100 mb-6">🚀 クイックアクション</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link to="/candidates" className="bg-gray-800 p-8 rounded-lg border border-gray-700 hover:border-gray-600 hover:-translate-y-1 transition-all duration-200 text-gray-100 no-underline group">
            <h3 className="text-xl font-semibold text-blue-400 mb-4 group-hover:text-blue-300">🎯 投資候補を見る</h3>
            <p className="text-gray-300 leading-relaxed">AI分析による投資候補銘柄をチェック</p>
          </Link>

          <Link to="/stocks" className="bg-gray-800 p-8 rounded-lg border border-gray-700 hover:border-gray-600 hover:-translate-y-1 transition-all duration-200 text-gray-100 no-underline group">
            <h3 className="text-xl font-semibold text-blue-400 mb-4 group-hover:text-blue-300">📊 銘柄検索</h3>
            <p className="text-gray-300 leading-relaxed">個別銘柄の詳細情報を確認</p>
          </Link>

          <Link to="/analysis" className="bg-gray-800 p-8 rounded-lg border border-gray-700 hover:border-gray-600 hover:-translate-y-1 transition-all duration-200 text-gray-100 no-underline group">
            <h3 className="text-xl font-semibold text-blue-400 mb-4 group-hover:text-blue-300">📈 市場分析</h3>
            <p className="text-gray-300 leading-relaxed">技術分析とトレンドを分析</p>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard