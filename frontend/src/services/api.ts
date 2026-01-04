import axios from 'axios'
import type {
  AuthStatusResponse,
  Invite,
  InviteCreateRequest,
  LoginRequest,
  RegisterRequest,
  User,
} from '../types/auth'
import type {
  BuyRequest,
  DepositRequest,
  PortfolioCreateRequest,
  PortfolioDetail,
  PortfolioSummary,
  PortfolioUpdateRequest,
  SellRequest,
  TransactionResponse,
  WithdrawalRequest,
} from '../types/portfolio'
import type {
  CandidatesCount,
  InvestmentCandidate,
  StockDetail,
  StockInfo,
  SystemStats,
  TechnicalAnalysis,
} from '../types/stock'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // セッションクッキーを送信するため
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

// 認証API
export const authApi = {
  // ログイン
  login: async (data: LoginRequest): Promise<User> => {
    const response = await api.post('/auth/login', data)
    return response.data
  },

  // ログアウト
  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  // 現在のユーザー取得
  me: async (): Promise<AuthStatusResponse> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  // 招待から登録
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },
}

// ユーザーAPI
export const usersApi = {
  // プロフィール更新
  updateProfile: async (display_name: string): Promise<User> => {
    const response = await api.put('/users/me', { display_name })
    return response.data
  },

  // パスワード変更
  changePassword: async (
    current_password: string,
    new_password: string,
  ): Promise<void> => {
    await api.post('/users/me/password', { current_password, new_password })
  },
}

// 管理者API
export const adminApi = {
  // ユーザー一覧取得
  listUsers: async (): Promise<User[]> => {
    const response = await api.get('/admin/users')
    return response.data
  },

  // ユーザー削除
  deleteUser: async (userId: number): Promise<void> => {
    await api.delete(`/admin/users/${userId}`)
  },

  // パスワードリセット
  resetPassword: async (
    userId: number,
    new_password: string,
  ): Promise<void> => {
    await api.post(`/admin/users/${userId}/reset-password`, { new_password })
  },

  // 招待作成
  createInvite: async (data: InviteCreateRequest): Promise<Invite> => {
    const response = await api.post('/admin/invites', data)
    return response.data
  },

  // 招待再発行
  reissueInvite: async (token: string): Promise<Invite> => {
    const response = await api.post(`/admin/invites/${token}/reissue`)
    return response.data
  },

  // 招待失効
  revokeInvite: async (token: string): Promise<void> => {
    await api.post(`/admin/invites/${token}/revoke`)
  },
}

// ポートフォリオAPI
export const portfolioApi = {
  // ポートフォリオ一覧取得
  getPortfolios: async (): Promise<PortfolioSummary[]> => {
    const response = await api.get('/portfolios/')
    return response.data
  },

  // ポートフォリオ詳細取得
  getPortfolioDetail: async (portfolioId: number): Promise<PortfolioDetail> => {
    const response = await api.get(`/portfolios/${portfolioId}`)
    return response.data
  },

  // ポートフォリオ作成
  createPortfolio: async (
    data: PortfolioCreateRequest,
  ): Promise<PortfolioDetail> => {
    const response = await api.post('/portfolios/', data)
    return response.data
  },

  // ポートフォリオ更新
  updatePortfolio: async (
    portfolioId: number,
    data: PortfolioUpdateRequest,
  ): Promise<PortfolioDetail> => {
    const response = await api.put(`/portfolios/${portfolioId}`, data)
    return response.data
  },

  // ポートフォリオ削除
  deletePortfolio: async (portfolioId: number): Promise<void> => {
    await api.delete(`/portfolios/${portfolioId}`)
  },

  // 銘柄購入
  buyStock: async (
    portfolioId: number,
    data: BuyRequest,
  ): Promise<TransactionResponse> => {
    const response = await api.post(
      `/portfolios/${portfolioId}/positions/buy`,
      data,
    )
    return response.data
  },

  // 銘柄売却
  sellStock: async (
    portfolioId: number,
    data: SellRequest,
  ): Promise<TransactionResponse> => {
    const response = await api.post(
      `/portfolios/${portfolioId}/positions/sell`,
      data,
    )
    return response.data
  },

  // 入金
  depositCash: async (
    portfolioId: number,
    data: DepositRequest,
  ): Promise<TransactionResponse> => {
    const response = await api.post(`/portfolios/${portfolioId}/deposit`, data)
    return response.data
  },

  // 出金
  withdrawCash: async (
    portfolioId: number,
    data: WithdrawalRequest,
  ): Promise<TransactionResponse> => {
    const response = await api.post(`/portfolios/${portfolioId}/withdraw`, data)
    return response.data
  },

  // 取引履歴取得
  getTransactions: async (
    portfolioId: number,
    params?: {
      start_date?: string
      end_date?: string
      symbol?: string
      transaction_type?: string
      limit?: number
    },
  ): Promise<TransactionResponse[]> => {
    const response = await api.get(`/portfolios/${portfolioId}/transactions`, {
      params,
    })
    return response.data
  },
}

// Companies API
export const companiesApi = {
  // 銘柄検索
  searchCompanies: async (
    search: string,
    limit: number = 50,
  ): Promise<
    Array<{
      symbol: string
      name: string | null
      sector: string | null
      market: string | null
    }>
  > => {
    const response = await api.get('/companies/', {
      params: { search, limit },
    })
    return response.data
  },
}

export default api
