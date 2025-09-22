import { useParams } from 'react-router-dom'

const StockDetail = () => {
  const { symbol } = useParams<{ symbol: string }>()

  return (
    <div className="stock-detail">
      <h1>📈 {symbol} - 銘柄詳細</h1>
      <p>個別銘柄の詳細情報とチャートを表示予定</p>
    </div>
  )
}

export default StockDetail