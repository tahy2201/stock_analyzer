import { ShoppingOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  message,
  Modal,
  Row,
  Select,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BuyModal from '../components/portfolio/BuyModal'
import { useAuth } from '../contexts/AuthContext'
import { portfolioApi, stockApi } from '../services/api'
import type { PortfolioSummary } from '../types/portfolio'
import type { StockInfo } from '../types/stock'
import { getYahooFinanceUrl } from '../utils/stockUtils'

// 銘柄一覧ページ
const StockList = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [limit, setLimit] = useState(100)
  const [form] = Form.useForm()

  // ポートフォリオ選択モーダル用の状態
  const [portfolioSelectVisible, setPortfolioSelectVisible] = useState(false)
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null)
  const [buyModalVisible, setBuyModalVisible] = useState(false)

  // ポートフォリオ一覧取得
  const { data: portfolios } = useQuery<PortfolioSummary[]>({
    queryKey: ['portfolios'],
    queryFn: portfolioApi.getPortfolios,
    enabled: !!user,
  })

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

  const columns: ColumnsType<StockInfo> = [
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
      dataIndex: 'current_price',
      key: 'current_price',
      width: 120,
      align: 'right',
      render: (price: number | null) =>
        price ? `¥${price.toLocaleString()}` : '---',
    },
    {
      title: '配当利回り',
      dataIndex: 'dividend_yield',
      key: 'dividend_yield',
      width: 120,
      align: 'right',
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

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h1 style={{ marginBottom: 16 }}>📊 銘柄一覧</h1>
        <p style={{ color: '#ff4d4f' }}>エラー: データの取得に失敗しました</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>📊 銘柄一覧</h1>
      <p style={{ marginBottom: 24, color: '#8c8c8c' }}>
        全銘柄の一覧を確認できます
      </p>

      {/* フィルターパネル */}
      <Card style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical">
          <Row gutter={[16, 24]}>
            <Col xs={24} sm={24} md={16}>
              <Form.Item label="検索" style={{ marginBottom: 0 }}>
                <Input
                  placeholder="銘柄コード・企業名・業種で検索..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  allowClear
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={24} md={8}>
              <Form.Item label="表示件数" style={{ marginBottom: 0 }}>
                <Select
                  style={{ width: '100%' }}
                  value={limit}
                  onChange={(value) => setLimit(value)}
                  options={[
                    { value: 50, label: '50件' },
                    { value: 100, label: '100件' },
                    { value: 200, label: '200件' },
                    { value: 500, label: '500件' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      <Table
        columns={columns}
        dataSource={filteredStocks}
        rowKey="symbol"
        loading={isLoading}
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

export default StockList
