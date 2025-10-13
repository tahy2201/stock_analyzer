import { Card, Col, Descriptions, Row, Spin, Statistic, Tag } from 'antd'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  LineChartOutlined,
} from '@ant-design/icons'

interface TickerInfo {
  trailing_pe: number | null
  forward_pe: number | null
  price_to_book: number | null
  return_on_equity: number | null
  return_on_assets: number | null
  debt_to_equity: number | null
  market_cap: number | null
  total_revenue: number | null
  earnings_growth: number | null
  revenue_growth: number | null
  profit_margins: number | null
  dividend_rate: number | null
  trailing_annual_dividend_rate: number | null
  ex_dividend_date: string | null
  fifty_two_week_high: number | null
  fifty_two_week_low: number | null
  average_volume: number | null
}

interface StockPrice {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface TechnicalIndicator {
  date: string
  ma_25: number | null
  divergence_rate: number | null
  volume_avg_20: number | null
}

interface StockDetailData {
  symbol: string
  name: string | null
  sector: string | null
  market: string | null
  current_price: number | null
  price_change: number | null
  price_change_percent: number | null
  dividend_yield: number | null
  prices: StockPrice[]
  technical_indicators: TechnicalIndicator[]
  ticker_info: TickerInfo | null
}

const StockDetail = () => {
  const { symbol } = useParams<{ symbol: string }>()
  const [stock, setStock] = useState<StockDetailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStockDetail = async () => {
      if (!symbol) return

      setLoading(true)
      setError(null)
      try {
        const response = await fetch(
          `http://localhost:8000/api/stocks/${symbol}`,
        )
        if (!response.ok) {
          throw new Error('銘柄データの取得に失敗しました')
        }
        const data = await response.json()
        setStock(data)
      } catch (err) {
        setError(
          err instanceof Error ? err.message : '不明なエラーが発生しました',
        )
      } finally {
        setLoading(false)
      }
    }

    fetchStockDetail()
  }, [symbol])

  // フォーマット用ヘルパー関数
  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '---'
    return value.toLocaleString()
  }

  const formatPercent = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '---'
    return `${(value * 100).toFixed(2)}%`
  }

  const formatCurrency = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '---'
    return `¥${value.toLocaleString()}`
  }

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (error || !stock) {
    return (
      <div style={{ padding: 24 }}>
        <h1>エラー</h1>
        <p style={{ color: '#ff4d4f' }}>{error || '銘柄が見つかりません'}</p>
      </div>
    )
  }

  const latestTechnical = stock.technical_indicators[stock.technical_indicators.length - 1]

  return (
    <div style={{ padding: 24 }}>
      {/* ヘッダー */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ marginBottom: 8 }}>
          <LineChartOutlined /> {stock.symbol} - {stock.name || '---'}
        </h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {stock.sector && <Tag>{stock.sector}</Tag>}
          {stock.market && (
            <Tag color={stock.market === 'prime' ? 'blue' : 'default'}>
              {stock.market}
            </Tag>
          )}
        </div>
      </div>

      {/* 基本情報 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="現在株価"
              value={stock.current_price || 0}
              prefix="¥"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="前日比"
              value={stock.price_change || 0}
              precision={2}
              valueStyle={{
                color:
                  stock.price_change && stock.price_change > 0
                    ? '#3f8600'
                    : '#cf1322',
              }}
              prefix={
                stock.price_change && stock.price_change > 0 ? (
                  <ArrowUpOutlined />
                ) : (
                  <ArrowDownOutlined />
                )
              }
              suffix={
                stock.price_change_percent
                  ? `(${stock.price_change_percent.toFixed(2)}%)`
                  : ''
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="配当利回り"
              value={stock.dividend_yield || 0}
              precision={2}
              suffix="%"
              valueStyle={{
                color: stock.dividend_yield && stock.dividend_yield >= 3 ? '#3f8600' : undefined,
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="乖離率"
              value={latestTechnical?.divergence_rate || 0}
              precision={2}
              suffix="%"
              valueStyle={{
                color:
                  latestTechnical?.divergence_rate && latestTechnical.divergence_rate < -5
                    ? '#cf1322'
                    : undefined,
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 投資指標 */}
      {stock.ticker_info && (
        <Card title="投資指標" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="PER (実績)">
                  {stock.ticker_info.trailing_pe?.toFixed(2) || '---'}
                </Descriptions.Item>
                <Descriptions.Item label="PER (予想)">
                  {stock.ticker_info.forward_pe?.toFixed(2) || '---'}
                </Descriptions.Item>
                <Descriptions.Item label="PBR">
                  {stock.ticker_info.price_to_book?.toFixed(2) || '---'}
                </Descriptions.Item>
                <Descriptions.Item label="ROE">
                  {formatPercent(stock.ticker_info.return_on_equity)}
                </Descriptions.Item>
                <Descriptions.Item label="ROA">
                  {formatPercent(stock.ticker_info.return_on_assets)}
                </Descriptions.Item>
              </Descriptions>
            </Col>
            <Col xs={24} md={12}>
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="時価総額">
                  {stock.ticker_info.market_cap
                    ? `¥${(stock.ticker_info.market_cap / 100000000).toFixed(0)}億`
                    : '---'}
                </Descriptions.Item>
                <Descriptions.Item label="負債比率">
                  {stock.ticker_info.debt_to_equity?.toFixed(2) || '---'}
                </Descriptions.Item>
                <Descriptions.Item label="52週高値">
                  {formatCurrency(stock.ticker_info.fifty_two_week_high)}
                </Descriptions.Item>
                <Descriptions.Item label="52週安値">
                  {formatCurrency(stock.ticker_info.fifty_two_week_low)}
                </Descriptions.Item>
                <Descriptions.Item label="平均出来高">
                  {formatNumber(stock.ticker_info.average_volume)}
                </Descriptions.Item>
              </Descriptions>
            </Col>
          </Row>
        </Card>
      )}

      {/* 財務情報 */}
      {stock.ticker_info && (
        <Card title="財務情報" style={{ marginBottom: 24 }}>
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="総売上">
              {stock.ticker_info.total_revenue
                ? `¥${(stock.ticker_info.total_revenue / 100000000).toFixed(0)}億`
                : '---'}
            </Descriptions.Item>
            <Descriptions.Item label="利益率">
              {formatPercent(stock.ticker_info.profit_margins)}
            </Descriptions.Item>
            <Descriptions.Item label="売上成長率">
              {formatPercent(stock.ticker_info.revenue_growth)}
            </Descriptions.Item>
            <Descriptions.Item label="利益成長率">
              {formatPercent(stock.ticker_info.earnings_growth)}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* 配当情報 */}
      {stock.ticker_info && (
        <Card title="配当情報" style={{ marginBottom: 24 }}>
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="年間配当金">
              {formatCurrency(stock.ticker_info.trailing_annual_dividend_rate)}
            </Descriptions.Item>
            <Descriptions.Item label="配当金（最新）">
              {formatCurrency(stock.ticker_info.dividend_rate)}
            </Descriptions.Item>
            <Descriptions.Item label="配当利回り">
              {stock.dividend_yield ? `${stock.dividend_yield.toFixed(2)}%` : '---'}
            </Descriptions.Item>
            <Descriptions.Item label="権利落ち日">
              {stock.ticker_info.ex_dividend_date || '---'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  )
}

export default StockDetail
