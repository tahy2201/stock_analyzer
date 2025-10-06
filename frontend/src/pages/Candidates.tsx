import { ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import {
  Button,
  Card,
  Col,
  Form,
  Row,
  Select,
  Slider,
  Space,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'

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

const Candidates = () => {
  const [candidates, setCandidates] = useState<InvestmentCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // フィルター状態
  const [minDividend, setMinDividend] = useState<number>(3.0)
  const [maxDivergence, setMaxDivergence] = useState<number>(-5.0)
  const [marketFilter, setMarketFilter] = useState<string>('prime')
  const [form] = Form.useForm()

  const columns: ColumnsType<InvestmentCandidate> = [
    {
      title: '銘柄コード',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      fixed: 'left',
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
      width: 100,
      align: 'right',
      sorter: (a, b) => (a.analysis_score || 0) - (b.analysis_score || 0),
      defaultSortOrder: 'descend',
      render: (score: number | null) => {
        if (score === null) return '0.0'
        const color = score >= 7 ? 'green' : score >= 5 ? 'blue' : 'default'
        return <Tag color={color}>{score.toFixed(1)}</Tag>
      },
    },
  ]

  // 投資候補データ取得
  const fetchCandidates = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        limit: '50',
        max_divergence: maxDivergence.toString(),
        min_dividend: minDividend.toString(),
        market_filter: marketFilter,
      })
      const response = await fetch(
        `http://localhost:8000/api/candidates/?${params}`,
      )
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
  }

  // 初回読み込み
  useEffect(() => {
    fetchCandidates()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 検索実行
  const handleSearch = () => {
    fetchCandidates()
  }

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
    // リセット後に自動で検索
    setTimeout(() => {
      fetchCandidates()
    }, 0)
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
              <Form.Item label={`配当利回り: ${minDividend}%以上`} name="minDividend">
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
              <Form.Item label={`乖離率: ${maxDivergence}%以下`} name="maxDivergence">
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
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  検索
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleReset}>
                  リセット
                </Button>
              </Space>
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
    </div>
  )
}

export default Candidates
