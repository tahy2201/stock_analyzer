import {
  ExperimentOutlined,
  ReloadOutlined,
  ShoppingOutlined,
} from '@ant-design/icons'
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
  Space,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import BuyModal from '../components/portfolio/BuyModal'
import AIAnalysisModal from '../components/stock/AIAnalysisModal'
import { useAuth } from '../contexts/AuthContext'
import { API_BASE_URL, portfolioApi } from '../services/api'
import type { PortfolioSummary } from '../types/portfolio'
import type { InvestmentCandidate } from '../types/stock'
import { getYahooFinanceUrl } from '../utils/stockUtils'

// デフォルト値
const DEFAULT_MIN_DIVIDEND = 3.0
const DEFAULT_MAX_DIVERGENCE = -5.0
const DEFAULT_MARKET_FILTER = 'prime'
const DEFAULT_MIN_SCORE = 0

// 投資候補ページ
const Candidates = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const [candidates, setCandidates] = useState<InvestmentCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // URLパラメータから初期値を取得
  const getInitialValue = (
    key: string,
    defaultValue: number | string,
  ): number | string => {
    const param = searchParams.get(key)
    if (param === null) return defaultValue
    if (typeof defaultValue === 'number') {
      const parsed = parseFloat(param)
      return isNaN(parsed) ? defaultValue : parsed
    }
    return param
  }

  // フィルター状態
  const [minDividend, setMinDividend] = useState<number>(
    getInitialValue('minDividend', DEFAULT_MIN_DIVIDEND) as number,
  )
  const [maxDivergence, setMaxDivergence] = useState<number>(
    getInitialValue('maxDivergence', DEFAULT_MAX_DIVERGENCE) as number,
  )
  const [marketFilter, setMarketFilter] = useState<string>(
    (getInitialValue('market', DEFAULT_MARKET_FILTER) as string) || '',
  )
  const [minScore, setMinScore] = useState<number>(
    getInitialValue('minScore', DEFAULT_MIN_SCORE) as number,
  )
  const [form] = Form.useForm()

  // ポートフォリオ選択モーダル用の状態
  const [portfolioSelectVisible, setPortfolioSelectVisible] = useState(false)
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(
    null,
  )
  const [buyModalVisible, setBuyModalVisible] = useState(false)

  // AI分析モーダル用の状態
  const [aiAnalysisVisible, setAiAnalysisVisible] = useState(false)
  const [aiAnalysisSymbol, setAiAnalysisSymbol] = useState<string>('')

  // URLパラメータが変わったらフォームの値も更新
  useEffect(() => {
    form.setFieldsValue({
      minDividend,
      maxDivergence,
      marketFilter,
      minScore,
    })
  }, [form, minDividend, maxDivergence, marketFilter, minScore])

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

  // AI分析ボタンハンドラ
  const handleAIAnalysis = (symbol: string) => {
    if (!user) {
      Modal.info({
        title: 'ログインが必要です',
        content: 'AI分析機能を使用するにはログインしてください。',
        onOk: () => navigate('/login'),
      })
      return
    }

    setAiAnalysisSymbol(symbol)
    setAiAnalysisVisible(true)
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
    {
      title: 'スコア',
      dataIndex: 'analysis_score',
      key: 'analysis_score',
      width: 90,
      align: 'right',
      sorter: (a, b) => (a.analysis_score || 0) - (b.analysis_score || 0),
      defaultSortOrder: 'descend',
      render: (score: number | null) => {
        if (score === null || score === undefined) return '---'
        let color = 'default'
        if (score >= 7) color = 'green'
        else if (score >= 5) color = 'blue'
        else if (score >= 3) color = 'orange'
        return <Tag color={color}>{score.toFixed(1)}</Tag>
      },
    },
  ]

  // ログイン時のみアクションカラムを追加
  if (user) {
    columns.push({
      title: 'アクション',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            icon={<ExperimentOutlined />}
            onClick={() => handleAIAnalysis(record.symbol)}
          >
            AI分析
          </Button>
          <Button
            type="primary"
            size="small"
            icon={<ShoppingOutlined />}
            onClick={() => handleBuy(record.symbol)}
          >
            購入
          </Button>
        </Space>
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
      // minScoreが0より大きい場合のみパラメータに追加
      if (minScore > 0) {
        params.append('min_score', minScore.toString())
      }
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
  }, [minDividend, maxDivergence, marketFilter, minScore])

  // フィルター値変更時に自動検索
  useEffect(() => {
    fetchCandidates()
  }, [fetchCandidates])

  // リセット
  const handleReset = () => {
    setMinDividend(DEFAULT_MIN_DIVIDEND)
    setMaxDivergence(DEFAULT_MAX_DIVERGENCE)
    setMarketFilter(DEFAULT_MARKET_FILTER)
    setMinScore(DEFAULT_MIN_SCORE)
    form.setFieldsValue({
      minDividend: DEFAULT_MIN_DIVIDEND,
      maxDivergence: DEFAULT_MAX_DIVERGENCE,
      marketFilter: DEFAULT_MARKET_FILTER,
      minScore: DEFAULT_MIN_SCORE,
    })
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ marginBottom: 16 }}>投資候補</h1>
        <p style={{ color: '#ff4d4f' }}>エラー: {error}</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>投資候補</h1>
      <p style={{ marginBottom: 24, color: '#8c8c8c' }}>
        技術分析に基づいた投資候補銘柄を検索できます
      </p>

      {/* フィルターパネル */}
      <Card style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            minDividend,
            maxDivergence,
            marketFilter,
            minScore,
          }}
        >
          <Row gutter={[16, 24]}>
            <Col xs={24} sm={12} md={6}>
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
            <Col xs={24} sm={12} md={6}>
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
            <Col xs={24} sm={12} md={6}>
              <Form.Item
                label={`最小スコア: ${minScore}`}
                name="minScore"
              >
                <Slider
                  min={0}
                  max={10}
                  step={1}
                  value={minScore}
                  onChange={(value) => setMinScore(value)}
                  marks={{
                    0: '0',
                    5: '5',
                    10: '10',
                  }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
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
        scroll={{ x: 1300 }}
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

      {/* AI分析モーダル */}
      <AIAnalysisModal
        visible={aiAnalysisVisible}
        symbol={aiAnalysisSymbol}
        onClose={() => {
          setAiAnalysisVisible(false)
          setAiAnalysisSymbol('')
        }}
      />
    </div>
  )
}

export default Candidates
