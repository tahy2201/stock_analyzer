import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { stockApi } from '../services/api'
import type { StockInfo } from '../types/stock'

const StockList = () => {
  const [limit, setLimit] = useState(100)
  const [searchTerm, setSearchTerm] = useState('')

  const { data: stocks, isLoading, error } = useQuery<StockInfo[]>({
    queryKey: ['stocks', limit],
    queryFn: () => stockApi.getStocks(limit),
  })

  // 検索フィルタリング
  const filteredStocks = stocks?.filter(stock =>
    stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.sector?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  if (isLoading) return <div>読み込み中...</div>
  if (error) return <div>エラーが発生しました</div>

  return (
    <div className="stock-list">
      <h1>📊 銘柄一覧</h1>

      {/* 検索とフィルター */}
      <div className="controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="銘柄コード・企業名・業種で検索..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="limit-selector">
          <label>表示件数: </label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="limit-select"
          >
            <option value={50}>50件</option>
            <option value={100}>100件</option>
            <option value={200}>200件</option>
            <option value={500}>500件</option>
          </select>
        </div>
      </div>

      {/* 統計情報 */}
      <div className="list-stats">
        <p>
          全{stocks?.length || 0}件中 {filteredStocks.length}件を表示
        </p>
      </div>

      {/* 銘柄テーブル */}
      <div className="table-container">
        <table className="stocks-table">
          <thead>
            <tr>
              <th>銘柄コード</th>
              <th>企業名</th>
              <th>業種</th>
              <th>市場</th>
              <th>現在価格</th>
              <th>配当利回り</th>
              <th>アクション</th>
            </tr>
          </thead>
          <tbody>
            {filteredStocks.map((stock) => (
              <tr key={stock.symbol}>
                <td className="symbol">{stock.symbol}</td>
                <td className="name">{stock.name || '-'}</td>
                <td className="sector">{stock.sector || '-'}</td>
                <td className="market">{stock.market || '-'}</td>
                <td className="price">
                  {stock.current_price ? `¥${stock.current_price.toLocaleString()}` : '-'}
                </td>
                <td className="dividend">
                  {stock.dividend_yield ? `${stock.dividend_yield}%` : '-'}
                </td>
                <td className="actions">
                  <Link
                    to={`/stocks/${stock.symbol}`}
                    className="detail-link"
                  >
                    詳細
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredStocks.length === 0 && searchTerm && (
        <div className="no-results">
          <p>「{searchTerm}」に該当する銘柄が見つかりませんでした。</p>
        </div>
      )}
    </div>
  )
}

export default StockList