import { ReloadOutlined, ShoppingOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  Form,
  Modal,
  message,
  Row,
  Select,
  Slider,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BuyModal from '../components/portfolio/BuyModal'
import { useAuth } from '../contexts/AuthContext'
import { API_BASE_URL, portfolioApi } from '../services/api'
import type { PortfolioSummary } from '../types/portfolio'
import { getYahooFinanceUrl } from '../utils/stockUtils'

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

// 投資候補ページ
const Candidates = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [candidates, setCandidates] = useState<InvestmentCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // フィルター状態
  const [minDividend, setMinDividend] = useState<number>(3.0)
  const [maxDivergence, setMaxDivergence] = useState<number>(-5.0)
  const [marketFilter, setMarketFilter] = useState<string>('prime')
  const [form] = Form.useForm()

  // ポートフォリオ選択モーダル用の状態
  const [portfolioSelectVisible, setPortfolioSelectVisible] = useState(false)
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(
    null,
  )
  const [buyModalVisible, setBuyModalVisible] = useState(false)

  // ポートフォリオ一覧取得
  const { data: portfolios } = useQuery<PortfolioSummary[]>({
    queryKey: ['portfolios'],
    queryFn: portfolioApi.getPortfolios,
    enabled: !!user,
  })

  // 購入ボタンハンドラ
  const handleBuy = (symbol: string) => {
    if (!user) {
      Modal.info({
        title: 'ログインが必要です',
        content: 'ポートフォリオ機能を使用するにはログインしてください。',
        onOk: () => navigate('/login'),
      })
      return
    }

    setSelectedSymbol(symbol)

    // ポートフォリオが1つもない場合
    if (!portfolios || portfolios.length === 0) {
      Modal.info({
        title: 'ポートフォリオがありません',
        content: 'まずポートフォリオを作成してください。',
        onOk: () => navigate('/portfolio'),
      })
      return
    }

    // ポートフォリオが1つだけの場合は直接購入モーダルを表示
    if (portfolios.length === 1) {
      setSelectedPortfolioId(portfolios[0].id)
      setBuyModalVisible(true)
      return
    }

    // 複数ある場合は選択モーダルを表示
    setSelectedPortfolioId(null) // 初期化
    setPortfolioSelectVisible(true)
  }

  // ポートフォリオ選択確定ハンドラ
  const handlePortfolioSelectOk = () => {
    if (!selectedPortfolioId) {
      message.warning('ポートフォリオを選択してください')
      return
    }
    setPortfolioSelectVisible(false)
    setBuyModalVisible(true)
  }

  const columns: ColumnsType<InvestmentCandidate> = [
    {
      title: '銘柄コード',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      fixed: 'left',
      render: (symbol: string) => (
        <a
          href={getYahooFinanceUrl(symbol)}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#1890ff', cursor: 'pointer' }}
        >
          {symbol}
        </a>
      ),
    },
    {
      title: '銘柄名',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (name: string | null) => name || '---',
    },
    {
      title: '業種',
      dataIndex: 'sector',
      key: 'sector',
      width: 150,
      render: (sector: string | null) => sector || '---',
    },
    {
      title: '市場',
      dataIndex: 'market',
      key: 'market',
      width: 100,
      render: (market: string | null) => (
        <Tag color={market === 'prime' ? 'blue' : 'default'}>
          {market || '---'}
        </Tag>
      ),
    },
    {
      title: '最新価格',
      dataIndex: 'latest_price',
      key: 'latest_price',
      width: 120,
      align: 'right',
      render: (price: number | null) =>
        price ? `¥${price.toLocaleString()}` : '---',
    },
    {
      title: '乖離率',
      dataIndex: 'divergence_rate',
      key: 'divergence_rate',
      width: 100,
      align: 'right',
      sorter: (a, b) => (a.divergence_rate || 0) - (b.divergence_rate || 0),
      render: (rate: number | null) => {
        if (rate === null) return '---'
        const color = rate < -10 ? 'red' : rate < -5 ? 'orange' : 'default'
        return <Tag color={color}>{rate.toFixed(2)}%</Tag>
      },
    },
    {
      title: '配当利回り',
      dataIndex: 'dividend_yield',
      key: 'dividend_yield',
      width: 120,
      align: 'right',
      sorter: (a, b) => (a.dividend_yield || 0) - (b.dividend_yield || 0),
      render: (yield_val: number | null) => {
        if (yield_val === null || yield_val === undefined) return '---'
        const color =
          yield_val >= 5 ? 'green' : yield_val >= 3 ? 'blue' : 'default'
        return <Tag color={color}>{yield_val.toFixed(2)}%</Tag>
      },
    },
  ]

  // ログイン時のみアクションカラムを追加
  if (user) {
    columns.push({
      title: 'アクション',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          icon={<ShoppingOutlined />}
          onClick={() => handleBuy(record.symbol)}
        >
          購入
        </Button>
      ),
    })
  }

  // 投資候補データ取得
  const fetchCandidates = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        limit: '50',
        max_divergence: maxDivergence.toString(),
        min_dividend: minDividend.toString(),
        market_filter: marketFilter,
      })
      const response = await fetch(`${API_BASE_URL}/candidates/?${params}`)
      if (!response.ok) {
        throw new Error('データの取得に失敗しました')
      }
      const data = await response.json()
      setCandidates(data)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : '不明なエラーが発生しました',
      )
    } finally {
      setLoading(false)
    }
  }, [minDividend, maxDivergence, marketFilter])

  // フィルター値変更時に自動検索
  useEffect(() => {
    fetchCandidates()
  }, [fetchCandidates])

  // リセット
  const handleReset = () => {
    setMinDividend(3.0)
    setMaxDivergence(-5.0)
    setMarketFilter('prime')
    form.setFieldsValue({
      minDividend: 3.0,
      maxDivergence: -5.0,
      marketFilter: 'prime',
    })
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ marginBottom: 16 }}>🎯 投資候補</h1>
        <p style={{ color: '#ff4d4f' }}>エラー: {error}</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>🎯 投資候補</h1>
      <p style={{ marginBottom: 24, color: '#8c8c8c' }}>
        技術分析に基づいた投資候補銘柄を検索できます
      </p>

      {/* フィルターパネル */}
      <Card style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            minDividend: 3.0,
            maxDivergence: -5.0,
            marketFilter: 'prime',
          }}
        >
          <Row gutter={[16, 24]}>
            <Col xs={24} sm={24} md={8}>
              <Form.Item
                label={`配当利回り: ${minDividend}%以上`}
                name="minDividend"
              >
                <Slider
                  min={0}
                  max={10}
                  step={0.5}
                  value={minDividend}
                  onChange={(value) => setMinDividend(value)}
                  marks={{
                    0: '0',
                    5: '5',
                    10: '10',
                  }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={8}>
              <Form.Item
                label={`乖離率: ${maxDivergence}%以下`}
                name="maxDivergence"
              >
                <Slider
                  min={-20}
                  max={0}
                  step={0.5}
                  value={maxDivergence}
                  onChange={(value) => setMaxDivergence(value)}
                  marks={{
                    '-20': '-20',
                    '-10': '-10',
                    0: '0',
                  }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={8}>
              <Form.Item label="市場区分" name="marketFilter">
                <Select
                  style={{ width: '100%' }}
                  value={marketFilter}
                  onChange={(value) => setMarketFilter(value)}
                  options={[
                    { value: 'prime', label: 'プライム' },
                    { value: 'standard', label: 'スタンダード' },
                    { value: 'growth', label: 'グロース' },
                    { value: '', label: '全て' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row style={{ marginTop: 16 }}>
            <Col span={24}>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                リセット
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>

      <Table
        columns={columns}
        dataSource={candidates}
        rowKey="symbol"
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `全${total}件`,
        }}
        scroll={{ x: 1200 }}
      />

      {/* ポートフォリオ選択モーダル */}
      <Modal
        title="ポートフォリオを選択"
        open={portfolioSelectVisible}
        onOk={handlePortfolioSelectOk}
        onCancel={() => setPortfolioSelectVisible(false)}
        okText="選択"
        cancelText="キャンセル"
      >
        <Select
          style={{ width: '100%' }}
          placeholder="ポートフォリオを選択してください"
          value={selectedPortfolioId}
          onChange={(value) => setSelectedPortfolioId(value)}
          options={portfolios?.map((portfolio) => ({
            value: portfolio.id,
            label: `${portfolio.name} (評価額: ¥${portfolio.total_value.toLocaleString()})`,
          }))}
        />
      </Modal>

      {/* 購入モーダル */}
      {selectedPortfolioId && selectedSymbol && (
        <BuyModal
          visible={buyModalVisible}
          portfolioId={selectedPortfolioId}
          onCancel={() => {
            setBuyModalVisible(false)
            setSelectedSymbol(null)
            setSelectedPortfolioId(null)
          }}
          initialSymbol={selectedSymbol}
        />
      )}
    </div>
  )
}

export default Candidates
