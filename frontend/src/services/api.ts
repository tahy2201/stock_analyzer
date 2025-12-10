import axios from 'axios'
import type {
  CandidatesCount,
  InvestmentCandidate,
  StockDetail,
  StockInfo,
  SystemStats,
  TechnicalAnalysis,
} from '../types/stock'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// 株式データAPI
export const stockApi = {
  // 全株式リスト取得
  getStocks: async (limit = 100): Promise<StockInfo[]> => {
    const response = await api.get(`/stocks?limit=${limit}`)
    return response.data
  },

  // 個別銘柄詳細取得
  getStockDetail: async (symbol: string, days = 100): Promise<StockDetail> => {
    const response = await api.get(`/stocks/${symbol}?days=${days}`)
    return response.data
  },

  // 株価データのみ取得
  getStockPrices: async (symbol: string, days = 100) => {
    const response = await api.get(`/stocks/${symbol}/prices?days=${days}`)
    return response.data
  },
}

// 投資候補API
export const candidatesApi = {
  // 投資候補一覧取得
  getCandidates: async (
    limit = 50,
    minDivergence = -10.0,
    minDividend = 1.0,
    maxDividend = 10.0,
  ): Promise<InvestmentCandidate[]> => {
    const response = await api.get(
      `/candidates?limit=${limit}&min_divergence=${minDivergence}&min_dividend=${minDividend}&max_dividend=${maxDividend}`,
    )
    return response.data
  },

  // 投資候補数統計取得
  getCandidatesCount: async (): Promise<CandidatesCount> => {
    const response = await api.get('/candidates/count')
    return response.data
  },
}

// 分析API
export const analysisApi = {
  // 技術分析取得
  getTechnicalAnalysis: async (symbol: string): Promise<TechnicalAnalysis> => {
    const response = await api.get(`/analysis/${symbol}`)
    return response.data
  },

  // システム統計取得
  getSystemStats: async (): Promise<SystemStats> => {
    const response = await api.get('/analysis/stats/system')
    return response.data
  },

  // 分析実行
  runAnalysis: async (symbol: string) => {
    const response = await api.post(`/analysis/run/${symbol}`)
    return response.data
  },
}

// ヘルスチェック
export const healthApi = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },
}

export default api
