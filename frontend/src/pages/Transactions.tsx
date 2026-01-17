import {
  ArrowLeftOutlined,
  FileTextOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Row,
  Select,
  Table,
  Tag,
  Tooltip,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { portfolioApi } from '../services/api'
import type { TransactionResponse } from '../types/portfolio'
import { getYahooFinanceUrl } from '../utils/stockUtils'

const { RangePicker } = DatePicker

const Transactions = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // フィルター状態
  const [filters, setFilters] = useState<{
    start_date?: string
    end_date?: string
    symbol?: string
    transaction_type?: string
  }>({})

  // 取引履歴取得
  const { data: transactions, isLoading } = useQuery<TransactionResponse[]>({
    queryKey: ['transactions', id, filters],
    queryFn: () => portfolioApi.getTransactions(Number(id), filters),
    enabled: !!id,
  })

  // フィルター適用
  const handleFilter = (values: {
    dateRange?: [dayjs.Dayjs, dayjs.Dayjs]
    symbol?: string
    transaction_type?: string
  }) => {
    const newFilters: typeof filters = {}

    if (values.dateRange && values.dateRange.length === 2) {
      newFilters.start_date = values.dateRange[0].startOf('day').toISOString()
      newFilters.end_date = values.dateRange[1].endOf('day').toISOString()
    }

    if (values.symbol) {
      newFilters.symbol = values.symbol
    }

    if (values.transaction_type) {
      newFilters.transaction_type = values.transaction_type
    }

    setFilters(newFilters)
  }

  // フィルターリセット
  const handleReset = () => {
    form.resetFields()
    setFilters({})
  }

  // 取引タイプのラベル取得
  const getTransactionTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      buy: '購入',
      sell: '売却',
      deposit: '入金',
      withdrawal: '出金',
    }
    return labels[type] || type
  }

  // 取引タイプのTagカラー
  const getTransactionTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      buy: 'success',
      sell: 'error',
      deposit: 'processing',
      withdrawal: 'warning',
    }
    return colors[type] || 'default'
  }

  // 損益の色を取得
  const getProfitColor = (profitLoss: number | null): string => {
    if (profitLoss === null) return '#8c8c8c'
    if (profitLoss > 0) return '#52c41a' // 緑
    if (profitLoss < 0) return '#ff4d4f' // 赤
    return '#8c8c8c' // グレー
  }

  // 銘柄の一意なリストを取得（フィルター用）
  const uniqueSymbols = Array.from(
    new Set(
      transactions
        ?.filter((t: TransactionResponse) => t.symbol !== null)
        .map((t: TransactionResponse) => t.symbol) || [],
    ),
  ).sort()

  // テーブルカラム定義
  const columns: ColumnsType<TransactionResponse> = [
    {
      title: '取引日時',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 180,
      sorter: (a: TransactionResponse, b: TransactionResponse) =>
        dayjs(a.transaction_date).unix() - dayjs(b.transaction_date).unix(),
      defaultSortOrder: 'descend',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '取引種別',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 100,
      render: (type: string) => (
        <Tag color={getTransactionTypeColor(type)}>
          {getTransactionTypeLabel(type)}
        </Tag>
      ),
    },
    {
      title: '銘柄コード',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol: string | null) =>
        symbol ? (
          <a
            href={getYahooFinanceUrl(symbol)}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: '#1890ff', cursor: 'pointer' }}
          >
            {symbol}
          </a>
        ) : (
          '---'
        ),
    },
    {
      title: '銘柄名',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 180,
      render: (name: string | null) => name || '---',
    },
    {
      title: '株数',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right',
      render: (quantity: number, record: TransactionResponse) =>
        record.transaction_type === 'buy' ||
        record.transaction_type === 'sell'
          ? `${quantity.toLocaleString()}株`
          : '---',
    },
    {
      title: '単価',
      dataIndex: 'price',
      key: 'price',
      width: 120,
      align: 'right',
      render: (price: number, record: TransactionResponse) =>
        record.transaction_type === 'buy' ||
        record.transaction_type === 'sell'
          ? `¥${price.toLocaleString()}`
          : '---',
    },
    {
      title: '金額',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 140,
      align: 'right',
      sorter: (a: TransactionResponse, b: TransactionResponse) =>
        a.total_amount - b.total_amount,
      render: (amount: number, record: TransactionResponse) => {
        const prefix =
          record.transaction_type === 'buy' ||
          record.transaction_type === 'withdrawal'
            ? '-'
            : '+'
        return (
          <span
            style={{
              color:
                record.transaction_type === 'buy' ||
                record.transaction_type === 'withdrawal'
                  ? '#ff4d4f'
                  : '#52c41a',
              fontWeight: 500,
            }}
          >
            {prefix}¥{amount.toLocaleString()}
          </span>
        )
      },
    },
    {
      title: '損益',
      dataIndex: 'profit_loss',
      key: 'profit_loss',
      width: 120,
      align: 'right',
      sorter: (a: TransactionResponse, b: TransactionResponse) =>
        (a.profit_loss || 0) - (b.profit_loss || 0),
      render: (profitLoss: number | null, record: TransactionResponse) => {
        if (record.transaction_type !== 'sell' || profitLoss === null) {
          return '---'
        }
        return (
          <span style={{ color: getProfitColor(profitLoss), fontWeight: 500 }}>
            {profitLoss >= 0 ? '+' : ''}¥{profitLoss.toLocaleString()}
          </span>
        )
      },
    },
    {
      title: 'メモ',
      dataIndex: 'notes',
      key: 'notes',
      width: 200,
      ellipsis: {
        showTitle: false,
      },
      render: (notes: string | null) =>
        notes ? (
          <Tooltip title={notes}>
            <span style={{ cursor: 'help' }}>
              <FileTextOutlined style={{ marginRight: 4 }} />
              {notes}
            </span>
          </Tooltip>
        ) : (
          <span style={{ color: '#8c8c8c' }}>---</span>
        ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* ヘッダー */}
      <div style={{ marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/portfolio/${id}`)}
          style={{ marginBottom: 16 }}
        >
          ポートフォリオに戻る
        </Button>
        <h1>取引履歴</h1>
      </div>

      {/* フィルター */}
      <Card
        title={
          <span>
            <FilterOutlined style={{ marginRight: 8 }} />
            フィルター
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFilter}
          initialValues={{}}
        >
          <Row gutter={16}>
            <Col xs={24} sm={12} lg={8}>
              <Form.Item label="取引期間" name="dateRange">
                <RangePicker
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD"
                  placeholder={['開始日', '終了日']}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Form.Item label="取引種別" name="transaction_type">
                <Select
                  placeholder="すべて"
                  allowClear
                  options={[
                    { value: 'buy', label: '購入' },
                    { value: 'sell', label: '売却' },
                    { value: 'deposit', label: '入金' },
                    { value: 'withdrawal', label: '出金' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Form.Item label="銘柄" name="symbol">
                <Select
                  placeholder="すべて"
                  allowClear
                  showSearch
                  options={uniqueSymbols.map((symbol) => ({
                    value: symbol,
                    label: symbol,
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row>
            <Col>
              <Button type="primary" htmlType="submit">
                適用
              </Button>
              <Button onClick={handleReset} style={{ marginLeft: 8 }}>
                リセット
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>

      {/* 取引履歴テーブル */}
      <Card title={`取引履歴（全${transactions?.length || 0}件）`}>
        {transactions && transactions.length > 0 ? (
          <Table
            columns={columns}
            dataSource={transactions}
            rowKey="id"
            loading={isLoading}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total: number) => `全${total}件`,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            scroll={{ x: 1400 }}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <p style={{ color: '#8c8c8c' }}>取引履歴がありません</p>
          </div>
        )}
      </Card>
    </div>
  )
}

export default Transactions
