export interface StockPrice {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface StockInfo {
  symbol: string
  name?: string
  sector?: string
  market?: string
  current_price?: number
  dividend_yield?: number
}

export interface StockDetail extends StockInfo {
  prices: StockPrice[]
}

export interface InvestmentCandidate {
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

export interface TechnicalAnalysis {
  symbol: string
  current_price?: number
  ma_25?: number
  divergence_rate?: number
  dividend_yield?: number
  volume_avg_20?: number
  ma_trend?: string
  price_trend?: string
  last_updated?: string
}

export interface SystemStats {
  companies_count: number
  symbols_with_prices: number
  symbols_with_technical: number
  latest_price_date?: string
  latest_analysis_date?: string
}

export interface CandidatesCount {
  total_candidates: number
  high_score: number
  medium_score: number
  low_score: number
}

export interface AIAnalysis {
  id: number
  symbol: string
  status: 'pending' | 'completed' | 'failed'
  analysis_text: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface AIAnalysisListResponse {
  analyses: AIAnalysis[]
  total: number
}
