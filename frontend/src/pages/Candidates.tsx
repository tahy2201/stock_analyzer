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
      <div className="candidates" style={{
        backgroundColor: '#1a1a1a',
        padding: '20px',
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <p>読み込み中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="candidates" style={{
        backgroundColor: '#1a1a1a',
        padding: '20px',
        minHeight: '100vh'
      }}>
        <h1>🎯 投資候補</h1>
        <p style={{ color: '#ff6b6b' }}>エラー: {error}</p>
      </div>
    )
  }

  return (
    <div className="candidates" style={{
      backgroundColor: '#1a1a1a',
      padding: '20px',
      minHeight: '100vh'
    }}>
      <h1>🎯 投資候補</h1>
      <p>25日移動平均線より5%以上下回る（乖離率-5%以下）、プライム企業</p>

      <div style={{ marginTop: '20px' }}>
        {candidates.length === 0 ? (
          <p>条件に合致する銘柄が見つかりませんでした</p>
        ) : (
          <div style={{
            display: 'grid',
            gap: '15px',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))'
          }}>
            {candidates.map((candidate) => (
              <div
                key={candidate.symbol}
                style={{
                  backgroundColor: '#2a2a2a',
                  padding: '15px',
                  borderRadius: '8px',
                  border: '1px solid #444'
                }}
              >
                <h3 style={{ margin: '0 0 10px 0', color: '#4a9eff' }}>
                  {candidate.symbol} - {candidate.name || '---'}
                </h3>
                <div style={{ fontSize: '14px', lineHeight: '1.4' }}>
                  <p><strong>業種:</strong> {candidate.sector || '---'}</p>
                  <p><strong>市場:</strong> {candidate.market || '---'}</p>
                  <p><strong>最新価格:</strong> {candidate.latest_price ? `¥${candidate.latest_price.toLocaleString()}` : '---'}</p>
                  <p><strong>乖離率:</strong> {candidate.divergence_rate ? `${candidate.divergence_rate.toFixed(2)}%` : '---'}</p>
                  <p><strong>配当利回り:</strong> {candidate.dividend_yield ? `${candidate.dividend_yield.toFixed(2)}%` : '---'}</p>
                  <p><strong>分析スコア:</strong> {candidate.analysis_score ? candidate.analysis_score.toFixed(1) : '0.0'}</p>
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