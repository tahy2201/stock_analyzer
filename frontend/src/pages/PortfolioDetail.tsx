import { ArrowLeftOutlined, ShoppingOutlined, DollarOutlined, HistoryOutlined, EditOutlined, PlusCircleOutlined, MinusCircleOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Col, DatePicker, Form, Input, InputNumber, message, Modal, Row, Statistic, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import BuyModal from '../components/portfolio/BuyModal'
import SellModal from '../components/portfolio/SellModal'
import { portfolioApi } from '../services/api'
import type { DepositRequest, PortfolioDetail as PortfolioDetailType, PortfolioUpdateRequest, PositionDetail, WithdrawalRequest } from '../types/portfolio'
import { getYahooFinanceUrl } from '../utils/stockUtils'

const PortfolioDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form] = Form.useForm()
  const [depositForm] = Form.useForm()
  const [withdrawForm] = Form.useForm()
  const [buyModalVisible, setBuyModalVisible] = useState(false)
  const [sellModalVisible, setSellModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [depositModalVisible, setDepositModalVisible] = useState(false)
  const [withdrawModalVisible, setWithdrawModalVisible] = useState(false)

  // ポートフォリオ詳細取得
  const { data: portfolio, isLoading } = useQuery<PortfolioDetailType>({
    queryKey: ['portfolio', id],
    queryFn: () => portfolioApi.getPortfolioDetail(Number(id)),
    enabled: !!id,
    refetchInterval: 30000, // 30秒ごとに自動リフレッシュ
  })

  // ポートフォリオ更新Mutation
  const updateMutation = useMutation({
    mutationFn: (data: PortfolioUpdateRequest) =>
      portfolioApi.updatePortfolio(Number(id), data),
    onSuccess: () => {
      message.success('ポートフォリオ情報を更新しました')
      queryClient.invalidateQueries({ queryKey: ['portfolio', id] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      setEditModalVisible(false)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'ポートフォリオの更新に失敗しました')
    },
  })

  // 編集モーダル表示時にフォームに値をセット
  useEffect(() => {
    if (editModalVisible && portfolio) {
      form.setFieldsValue({
        name: portfolio.name,
        description: portfolio.description || '',
        initial_capital: portfolio.initial_capital,
      })
    }
  }, [editModalVisible, portfolio, form])

  // 編集実行
  const handleUpdate = () => {
    form.validateFields().then((values) => {
      updateMutation.mutate(values)
    })
  }

  // 入金Mutation
  const depositMutation = useMutation({
    mutationFn: (data: DepositRequest) =>
      portfolioApi.depositCash(Number(id), data),
    onSuccess: () => {
      message.success('入金しました')
      queryClient.invalidateQueries({ queryKey: ['portfolio', id] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      depositForm.resetFields()
      setDepositModalVisible(false)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '入金に失敗しました')
    },
  })

  // 出金Mutation
  const withdrawMutation = useMutation({
    mutationFn: (data: WithdrawalRequest) =>
      portfolioApi.withdrawCash(Number(id), data),
    onSuccess: () => {
      message.success('出金しました')
      queryClient.invalidateQueries({ queryKey: ['portfolio', id] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      withdrawForm.resetFields()
      setWithdrawModalVisible(false)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '出金に失敗しました')
    },
  })

  // 入金実行
  const handleDeposit = () => {
    depositForm.validateFields().then((values) => {
      const depositRequest: DepositRequest = {
        amount: values.amount,
        transaction_date: values.transaction_date
          ? values.transaction_date.toISOString()
          : null,
        notes: values.notes || null,
      }
      depositMutation.mutate(depositRequest)
    })
  }

  // 出金実行
  const handleWithdraw = () => {
    withdrawForm.validateFields().then((values) => {
      const withdrawRequest: WithdrawalRequest = {
        amount: values.amount,
        transaction_date: values.transaction_date
          ? values.transaction_date.toISOString()
          : null,
        notes: values.notes || null,
      }
      withdrawMutation.mutate(withdrawRequest)
    })
  }

  // 損益の色を取得
  const getProfitColor = (profitLoss: number | null): string => {
    if (profitLoss === null) return '#8c8c8c'
    if (profitLoss > 0) return '#52c41a' // 緑
    if (profitLoss < 0) return '#ff4d4f' // 赤
    return '#8c8c8c' // グレー
  }

  // 損益率のTagカラー
  const getProfitRateTagColor = (rate: number | null): string => {
    if (rate === null) return 'default'
    if (rate > 0) return 'success'
    if (rate < 0) return 'error'
    return 'default'
  }

  // 保有銘柄テーブルカラム定義
  const columns: ColumnsType<PositionDetail> = [
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
      dataIndex: 'company_name',
      key: 'company_name',
      width: 180,
      render: (name: string | null) => name || '---',
    },
    {
      title: '保有株数',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right',
      render: (quantity: number) => `${quantity.toLocaleString()}株`,
    },
    {
      title: '平均取得単価',
      dataIndex: 'average_price',
      key: 'average_price',
      width: 120,
      align: 'right',
      render: (price: number) => `¥${price.toLocaleString()}`,
    },
    {
      title: '現在株価',
      dataIndex: 'current_price',
      key: 'current_price',
      width: 120,
      align: 'right',
      render: (price: number | null) =>
        price !== null ? `¥${price.toLocaleString()}` : '---',
    },
    {
      title: '取得金額',
      dataIndex: 'total_cost',
      key: 'total_cost',
      width: 120,
      align: 'right',
      render: (cost: number) => `¥${cost.toLocaleString()}`,
    },
    {
      title: '評価額',
      dataIndex: 'current_value',
      key: 'current_value',
      width: 120,
      align: 'right',
      render: (value: number | null) =>
        value !== null ? `¥${value.toLocaleString()}` : '---',
    },
    {
      title: '損益',
      dataIndex: 'profit_loss',
      key: 'profit_loss',
      width: 120,
      align: 'right',
      sorter: (a, b) => (a.profit_loss || 0) - (b.profit_loss || 0),
      render: (profitLoss: number | null) => {
        if (profitLoss === null) return '---'
        return (
          <span style={{ color: getProfitColor(profitLoss), fontWeight: 500 }}>
            {profitLoss >= 0 ? '+' : ''}
            ¥{profitLoss.toLocaleString()}
          </span>
        )
      },
    },
    {
      title: '損益率',
      dataIndex: 'profit_loss_rate',
      key: 'profit_loss_rate',
      width: 100,
      align: 'right',
      sorter: (a, b) => (a.profit_loss_rate || 0) - (b.profit_loss_rate || 0),
      render: (rate: number | null) => {
        if (rate === null) return '---'
        return (
          <Tag color={getProfitRateTagColor(rate)}>
            {rate >= 0 ? '+' : ''}
            {rate.toFixed(2)}%
          </Tag>
        )
      },
    },
  ]

  if (isLoading || !portfolio) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <p>読み込み中...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* ヘッダー */}
      <div style={{ marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/portfolio')}
          style={{ marginBottom: 16 }}
        >
          戻る
        </Button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <h1 style={{ marginBottom: 8 }}>{portfolio.name}</h1>
              <Button
                icon={<EditOutlined />}
                onClick={() => setEditModalVisible(true)}
                size="small"
              >
                編集
              </Button>
            </div>
            <p style={{ color: '#8c8c8c', marginBottom: 0 }}>
              {portfolio.description || '説明なし'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              type="primary"
              icon={<ShoppingOutlined />}
              onClick={() => setBuyModalVisible(true)}
            >
              購入
            </Button>
            <Button
              icon={<DollarOutlined />}
              onClick={() => setSellModalVisible(true)}
            >
              売却
            </Button>
            <Button
              icon={<HistoryOutlined />}
              onClick={() => navigate(`/portfolio/${id}/transactions`)}
            >
              取引履歴
            </Button>
          </div>
        </div>
      </div>

      {/* サマリーカード */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="総評価額"
              value={portfolio.total_value}
              precision={0}
              suffix="円"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="総損益"
              value={portfolio.total_profit_loss}
              precision={0}
              suffix="円"
              valueStyle={{ color: getProfitColor(portfolio.total_profit_loss) }}
              prefix={portfolio.total_profit_loss >= 0 ? '+' : ''}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="損益率"
              value={portfolio.total_profit_loss_rate}
              precision={2}
              suffix="%"
              valueStyle={{ color: getProfitColor(portfolio.total_profit_loss) }}
              prefix={portfolio.total_profit_loss_rate >= 0 ? '+' : ''}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="現金残高"
              value={portfolio.cash_balance}
              precision={0}
              suffix="円"
            />
            <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
              <Button
                size="small"
                icon={<PlusCircleOutlined />}
                onClick={() => setDepositModalVisible(true)}
              >
                入金
              </Button>
              <Button
                size="small"
                icon={<MinusCircleOutlined />}
                onClick={() => setWithdrawModalVisible(true)}
              >
                出金
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 保有銘柄テーブル */}
      <Card title="保有銘柄" style={{ marginBottom: 24 }}>
        {portfolio.positions.length > 0 ? (
          <Table
            columns={columns}
            dataSource={portfolio.positions}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `全${total}銘柄`,
            }}
            scroll={{ x: 1200 }}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <p style={{ color: '#8c8c8c', marginBottom: 16 }}>
              まだ保有銘柄がありません
            </p>
            <Button
              type="primary"
              icon={<ShoppingOutlined />}
              onClick={() => setBuyModalVisible(true)}
            >
              最初の銘柄を購入
            </Button>
          </div>
        )}
      </Card>

      <BuyModal
        visible={buyModalVisible}
        portfolioId={Number(id)}
        onCancel={() => setBuyModalVisible(false)}
      />
      <SellModal
        visible={sellModalVisible}
        portfolioId={Number(id)}
        positions={portfolio.positions}
        onCancel={() => setSellModalVisible(false)}
      />

      {/* 編集モーダル */}
      <Modal
        title="ポートフォリオ編集"
        open={editModalVisible}
        onOk={handleUpdate}
        onCancel={() => setEditModalVisible(false)}
        okText="更新"
        cancelText="キャンセル"
        confirmLoading={updateMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            label="ポートフォリオ名"
            name="name"
            rules={[
              { required: true, message: 'ポートフォリオ名を入力してください' },
              { max: 100, message: '100文字以内で入力してください' },
            ]}
          >
            <Input placeholder="例: 高配当株ポートフォリオ" />
          </Form.Item>

          <Form.Item
            label="説明（任意）"
            name="description"
            rules={[{ max: 500, message: '500文字以内で入力してください' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="例: 配当利回り4%以上の銘柄を中心に構成"
            />
          </Form.Item>

          <Form.Item
            label="初期資本金"
            name="initial_capital"
            rules={[
              { required: true, message: '初期資本金を入力してください' },
              { type: 'number', min: 0.01, message: '0より大きい値を入力してください' },
            ]}
            help="現金残高は「初期資本金 - 総購入額 + 総売却額」で計算されます"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.01}
              step={10000}
              precision={2}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value?.replace(/¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 入金モーダル */}
      <Modal
        title="現金入金"
        open={depositModalVisible}
        onOk={handleDeposit}
        onCancel={() => setDepositModalVisible(false)}
        okText="入金"
        cancelText="キャンセル"
        confirmLoading={depositMutation.isPending}
        width={500}
      >
        <Form
          form={depositForm}
          layout="vertical"
          initialValues={{
            amount: 100000,
          }}
        >
          <Form.Item
            label="入金額"
            name="amount"
            rules={[
              { required: true, message: '入金額を入力してください' },
              { type: 'number', min: 0.01, message: '0より大きい値を入力してください' },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.01}
              step={10000}
              precision={2}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value?.replace(/¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>

          <Form.Item
            label="取引日時"
            name="transaction_date"
            help="未入力の場合は現在日時が使用されます"
          >
            <DatePicker
              showTime
              style={{ width: '100%' }}
              format="YYYY-MM-DD HH:mm:ss"
              placeholder="取引日時を選択"
              disabledDate={(current) => current && current > dayjs().endOf('day')}
            />
          </Form.Item>

          <Form.Item
            label="メモ（任意）"
            name="notes"
            rules={[{ max: 500, message: '500文字以内で入力してください' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="例: ボーナス入金"
              maxLength={500}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 出金モーダル */}
      <Modal
        title="現金出金"
        open={withdrawModalVisible}
        onOk={handleWithdraw}
        onCancel={() => setWithdrawModalVisible(false)}
        okText="出金"
        cancelText="キャンセル"
        confirmLoading={withdrawMutation.isPending}
        width={500}
      >
        <Form
          form={withdrawForm}
          layout="vertical"
          initialValues={{
            amount: 100000,
          }}
        >
          <Form.Item
            label="出金額"
            name="amount"
            rules={[
              { required: true, message: '出金額を入力してください' },
              { type: 'number', min: 0.01, message: '0より大きい値を入力してください' },
            ]}
            help={portfolio ? `現在の現金残高: ¥${portfolio.cash_balance.toLocaleString()}` : ''}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.01}
              step={10000}
              precision={2}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value?.replace(/¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>

          <Form.Item
            label="取引日時"
            name="transaction_date"
            help="未入力の場合は現在日時が使用されます"
          >
            <DatePicker
              showTime
              style={{ width: '100%' }}
              format="YYYY-MM-DD HH:mm:ss"
              placeholder="取引日時を選択"
              disabledDate={(current) => current && current > dayjs().endOf('day')}
            />
          </Form.Item>

          <Form.Item
            label="メモ（任意）"
            name="notes"
            rules={[{ max: 500, message: '500文字以内で入力してください' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="例: 生活費として出金"
              maxLength={500}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PortfolioDetail
