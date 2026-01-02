/**
 * Portfolio-related type definitions
 */

export interface PortfolioCreateRequest {
  name: string
  description?: string | null
  initial_capital: number
}

export interface PortfolioUpdateRequest {
  name?: string | null
  description?: string | null
  initial_capital?: number | null
}

export interface PortfolioSummary {
  id: number
  name: string
  description: string | null
  initial_capital: number
  total_value: number
  total_profit_loss: number
  total_profit_loss_rate: number
  cash_balance: number
  positions_count: number
  created_at: string
  updated_at: string
}

export interface PositionDetail {
  id: number
  symbol: string
  company_name: string | null
  quantity: number
  average_price: number
  current_price: number | null
  total_cost: number
  current_value: number | null
  profit_loss: number | null
  profit_loss_rate: number | null
  created_at: string
  updated_at: string
}

export interface PortfolioDetail {
  id: number
  name: string
  description: string | null
  initial_capital: number
  total_value: number
  total_profit_loss: number
  total_profit_loss_rate: number
  cash_balance: number
  positions: PositionDetail[]
  created_at: string
  updated_at: string
}

export interface BuyRequest {
  symbol: string
  quantity: number
  price?: number | null
  transaction_date?: string | null
  notes?: string | null
}

export interface SellRequest {
  symbol: string
  quantity: number
  price?: number | null
  transaction_date?: string | null
  notes?: string | null
}

export interface DepositRequest {
  amount: number
  transaction_date?: string | null
  notes?: string | null
}

export interface WithdrawalRequest {
  amount: number
  transaction_date?: string | null
  notes?: string | null
}

export interface TransactionResponse {
  id: number
  symbol: string | null
  company_name: string | null
  transaction_type: string
  quantity: number
  price: number
  total_amount: number
  profit_loss: number | null
  transaction_date: string
  created_at: string
  notes: string | null
}
