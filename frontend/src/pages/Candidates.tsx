import { useEffect, useState } from 'react'

interface InvestmentCandidate {
  symbol: string
  name: string | null
  sector: string | null
  market: string | null
  current_price: number | null
  ma_25: number | null
  divergence_rate: number | null
  dividend_yield: number | null
  analysis_score: number | null
  latest_price: number | null
  price_change_1d: number | null
}

const Candidates = () => {
  const [candidates, setCandidates] = useState<InvestmentCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/candidates/?limit=10&max_divergence=-5.0&min_dividend=0.0&market_filter=prime')
        if (!response.ok) {
          throw new Error('データの取得に失敗しました')
        }
        const data = await response.json()
        setCandidates(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました')
      } finally {
        setLoading(false)
      }
    }

    fetchCandidates()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-5">
        <p className="text-gray-100">読み込み中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 p-5">
        <h1 className="text-2xl font-bold text-gray-100 mb-4">🎯 投資候補</h1>
        <p className="text-red-400">エラー: {error}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 p-5">
      <h1 className="text-3xl font-bold text-gray-100 mb-2">🎯 投資候補</h1>
      <p className="text-gray-300 mb-5">25日移動平均線より5%以上下回る（乖離率-5%以下）、プライム企業</p>

      <div className="mt-5">
        {candidates.length === 0 ? (
          <p className="text-gray-400">条件に合致する銘柄が見つかりませんでした</p>
        ) : (
          <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(300px,1fr))]">
            {candidates.map((candidate) => (
              <div
                key={candidate.symbol}
                className="bg-gray-800 p-4 rounded-lg border border-gray-600 hover:border-gray-500 transition-colors"
              >
                <h3 className="text-blue-400 font-semibold mb-3 text-lg">
                  {candidate.symbol} - {candidate.name || '---'}
                </h3>
                <div className="text-sm space-y-2 text-gray-300">
                  <p><span className="font-medium text-gray-100">業種:</span> {candidate.sector || '---'}</p>
                  <p><span className="font-medium text-gray-100">市場:</span> {candidate.market || '---'}</p>
                  <p><span className="font-medium text-gray-100">最新価格:</span> {candidate.latest_price ? `¥${candidate.latest_price.toLocaleString()}` : '---'}</p>
                  <p><span className="font-medium text-gray-100">乖離率:</span> {candidate.divergence_rate ? `${candidate.divergence_rate.toFixed(2)}%` : '---'}</p>
                  <p><span className="font-medium text-gray-100">配当利回り:</span> {candidate.dividend_yield !== null && candidate.dividend_yield !== undefined ? `${candidate.dividend_yield.toFixed(2)}%` : '---'}</p>
                  <p><span className="font-medium text-gray-100">分析スコア:</span> {candidate.analysis_score ? candidate.analysis_score.toFixed(1) : '0.0'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Candidates