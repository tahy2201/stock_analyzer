import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Statistic,
  Tag,
} from 'antd'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { portfolioApi } from '../services/api'
import type { PortfolioCreateRequest, PortfolioSummary } from '../types/portfolio'

const Portfolio = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  // ポートフォリオ一覧取得
  const { data: portfolios, isLoading } = useQuery<PortfolioSummary[]>({
    queryKey: ['portfolios'],
    queryFn: portfolioApi.getPortfolios,
  })

  // ポートフォリオ作成Mutation
  const createMutation = useMutation({
    mutationFn: (data: PortfolioCreateRequest) => portfolioApi.createPortfolio(data),
    onSuccess: () => {
      message.success('ポートフォリオを作成しました')
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      setCreateModalVisible(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'ポートフォリオの作成に失敗しました')
    },
  })

  // ポートフォリオ削除Mutation
  const deleteMutation = useMutation({
    mutationFn: (portfolioId: number) => portfolioApi.deletePortfolio(portfolioId),
    onSuccess: () => {
      message.success('ポートフォリオを削除しました')
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'ポートフォリオの削除に失敗しました')
    },
  })

  // 作成ボタンハンドラ
  const handleCreate = () => {
    form.validateFields().then((values) => {
      createMutation.mutate(values)
    })
  }

  // 削除確認
  const handleDelete = (portfolio: PortfolioSummary) => {
    Modal.confirm({
      title: 'ポートフォリオを削除しますか？',
      content: `「${portfolio.name}」を削除すると、保有銘柄と取引履歴も全て削除されます。この操作は取り消せません。`,
      okText: '削除',
      okType: 'danger',
      cancelText: 'キャンセル',
      onOk: () => deleteMutation.mutate(portfolio.id),
    })
  }

  // 損益の色を取得
  const getProfitColor = (profitLoss: number): string => {
    if (profitLoss > 0) return '#52c41a' // 緑
    if (profitLoss < 0) return '#ff4d4f' // 赤
    return '#8c8c8c' // グレー
  }

  // 損益率のTagカラー
  const getProfitRateTagColor = (rate: number): string => {
    if (rate > 0) return 'success'
    if (rate < 0) return 'error'
    return 'default'
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ marginBottom: 8 }}>💼 ポートフォリオ</h1>
          <p style={{ marginBottom: 0, color: '#8c8c8c' }}>
            仮想売買で銘柄の損益を管理できます（最大10個まで）
          </p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
          disabled={portfolios && portfolios.length >= 10}
        >
          新規作成
        </Button>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <p>読み込み中...</p>
        </div>
      ) : portfolios && portfolios.length > 0 ? (
        <Row gutter={[16, 16]}>
          {portfolios.map((portfolio) => (
            <Col key={portfolio.id} xs={24} sm={12} lg={8} xl={6}>
              <Card
                hoverable
                onClick={() => navigate(`/portfolio/${portfolio.id}`)}
                style={{ height: '100%', cursor: 'pointer' }}
                actions={[
                  <EditOutlined
                    key="edit"
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/portfolio/${portfolio.id}`)
                    }}
                  />,
                  <DeleteOutlined
                    key="delete"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(portfolio)
                    }}
                  />,
                ]}
              >
                <Card.Meta
                  title={<span style={{ fontSize: 16 }}>{portfolio.name}</span>}
                  description={
                    <div style={{ fontSize: 12, color: '#8c8c8c', minHeight: 40 }}>
                      {portfolio.description || '説明なし'}
                    </div>
                  }
                />
                <div style={{ marginTop: 16 }}>
                  <Statistic
                    title="総評価額"
                    value={portfolio.total_value}
                    precision={0}
                    suffix="円"
                    valueStyle={{ fontSize: 20 }}
                  />
                  <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 12, color: '#8c8c8c' }}>損益</div>
                      <div style={{ fontSize: 16, fontWeight: 500, color: getProfitColor(portfolio.total_profit_loss) }}>
                        {portfolio.total_profit_loss >= 0 ? '+' : ''}
                        {portfolio.total_profit_loss.toLocaleString()}円
                      </div>
                    </div>
                    <Tag color={getProfitRateTagColor(portfolio.total_profit_loss_rate)}>
                      {portfolio.total_profit_loss_rate >= 0 ? '+' : ''}
                      {portfolio.total_profit_loss_rate.toFixed(2)}%
                    </Tag>
                  </div>
                  <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
                    <Row gutter={8}>
                      <Col span={12}>
                        <div style={{ fontSize: 12, color: '#8c8c8c' }}>現金残高</div>
                        <div style={{ fontSize: 14 }}>{portfolio.cash_balance.toLocaleString()}円</div>
                      </Col>
                      <Col span={12}>
                        <div style={{ fontSize: 12, color: '#8c8c8c' }}>保有銘柄</div>
                        <div style={{ fontSize: 14 }}>{portfolio.positions_count}銘柄</div>
                      </Col>
                    </Row>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Card style={{ textAlign: 'center', padding: 60 }}>
          <p style={{ fontSize: 16, color: '#8c8c8c', marginBottom: 16 }}>
            まだポートフォリオがありません
          </p>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            最初のポートフォリオを作成
          </Button>
        </Card>
      )}

      {/* 作成モーダル */}
      <Modal
        title="ポートフォリオを作成"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        okText="作成"
        cancelText="キャンセル"
        confirmLoading={createMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            initial_capital: 1000000,
          }}
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
              placeholder="例: 配当利回り3%以上の銘柄を中心に運用"
            />
          </Form.Item>

          <Form.Item
            label="初期資本金"
            name="initial_capital"
            rules={[
              { required: true, message: '初期資本金を入力してください' },
              { type: 'number', min: 1, message: '1円以上の金額を入力してください' },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              step={100000}
              formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value) => value?.replace(/¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Portfolio
