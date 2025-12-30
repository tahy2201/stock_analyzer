import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { stockApi } from '../services/api'
import type { StockInfo } from '../types/stock'
import { getYahooFinanceUrl } from '../utils/stockUtils'

const StockList = () => {
  const [limit, setLimit] = useState(100)
  const [searchTerm, setSearchTerm] = useState('')

  const {
    data: stocks,
    isLoading,
    error,
  } = useQuery<StockInfo[]>({
    queryKey: ['stocks', limit],
    queryFn: () => stockApi.getStocks(limit),
  })

  // 検索フィルタリング
  const filteredStocks =
    stocks?.filter(
      (stock) =>
        stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.sector?.toLowerCase().includes(searchTerm.toLowerCase()),
    ) || []

  if (isLoading)
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-gray-400">読み込み中...</div>
      </div>
    )
  if (error)
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-red-400">エラーが発生しました</div>
      </div>
    )

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-6">📊 銘柄一覧</h1>

      {/* 検索とフィルター */}
      <div className="flex flex-col md:flex-row gap-4 mb-6 items-start md:items-center">
        <div className="flex-1 min-w-64">
          <input
            type="text"
            placeholder="銘柄コード・企業名・業種で検索..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 text-gray-300">
          <label>表示件数: </label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-2 bg-gray-800 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:border-blue-500"
          >
            <option value={50}>50件</option>
            <option value={100}>100件</option>
            <option value={200}>200件</option>
            <option value={500}>500件</option>
          </select>
        </div>
      </div>

      {/* 統計情報 */}
      <div className="mb-4">
        <p className="text-gray-400">
          全{stocks?.length || 0}件中 {filteredStocks.length}件を表示
        </p>
      </div>

      {/* 銘柄テーブル */}
      <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-700 border-b border-gray-600">
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  銘柄コード
                </th>
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  企業名
                </th>
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  業種
                </th>
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  市場
                </th>
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  現在価格
                </th>
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  配当利回り
                </th>
                <th className="px-4 py-4 text-left font-semibold text-gray-200">
                  アクション
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredStocks.map((stock) => (
                <tr
                  key={stock.symbol}
                  className="border-b border-gray-700 hover:bg-gray-750 transition-colors"
                >
                  <td className="px-4 py-4 font-mono font-semibold text-blue-400">
                    <a
                      href={getYahooFinanceUrl(stock.symbol)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 hover:underline transition-colors cursor-pointer"
                    >
                      {stock.symbol}
                    </a>
                  </td>
                  <td className="px-4 py-4 text-gray-100">
                    {stock.name || '-'}
                  </td>
                  <td className="px-4 py-4 text-gray-300">
                    {stock.sector || '-'}
                  </td>
                  <td className="px-4 py-4 text-gray-300">
                    {stock.market || '-'}
                  </td>
                  <td className="px-4 py-4 font-semibold text-green-400">
                    {stock.current_price
                      ? `¥${stock.current_price.toLocaleString()}`
                      : '-'}
                  </td>
                  <td className="px-4 py-4 font-medium text-red-400">
                    {stock.dividend_yield ? `${stock.dividend_yield}%` : '-'}
                  </td>
                  <td className="px-4 py-4">
                    <a
                      href={getYahooFinanceUrl(stock.symbol)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                      詳細
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {filteredStocks.length === 0 && searchTerm && (
        <div className="text-center py-12">
          <p className="text-gray-400">
            「{searchTerm}」に該当する銘柄が見つかりませんでした。
          </p>
        </div>
      )}
    </div>
  )
}

export default StockList
