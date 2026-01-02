import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Select,
  Space,
} from 'antd'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'
import { companiesApi, portfolioApi } from '../../services/api'
import type { BuyRequest } from '../../types/portfolio'

interface BuyModalProps {
  visible: boolean
  portfolioId: number
  onCancel: () => void
  initialSymbol?: string
}

interface Company {
  symbol: string
  name: string | null
  sector: string | null
  market: string | null
}

const BuyModal = ({ visible, portfolioId, onCancel, initialSymbol }: BuyModalProps) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')

  // モーダルが開かれたときにinitialSymbolをセット
  useEffect(() => {
    if (visible && initialSymbol) {
      form.setFieldValue('symbol', initialSymbol)
    }
  }, [visible, initialSymbol, form])

  // 銘柄一覧取得（検索用）
  const { data: companies, isLoading: isLoadingCompanies } = useQuery<Company[]>({
    queryKey: ['companies', searchQuery],
    queryFn: () => companiesApi.searchCompanies(searchQuery, 50),
    enabled: visible && searchQuery.length > 0,
  })

  // 購入Mutation
  const buyMutation = useMutation({
    mutationFn: (data: BuyRequest) => portfolioApi.buyStock(portfolioId, data),
    onSuccess: () => {
      message.success('銘柄を購入しました')
      queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId.toString()] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '銘柄の購入に失敗しました')
    },
  })

  // 購入実行
  const handleBuy = () => {
    form.validateFields().then((values) => {
      const buyRequest: BuyRequest = {
        symbol: values.symbol,
        quantity: values.quantity,
        price: values.price || null,
        transaction_date: values.transaction_date
          ? values.transaction_date.toISOString()
          : null,
        notes: values.notes || null,
      }
      buyMutation.mutate(buyRequest)
    })
  }

  // モーダルキャンセル
  const handleCancel = () => {
    form.resetFields()
    setSearchQuery('')
    onCancel()
  }

  return (
    <Modal
      title="銘柄を購入"
      open={visible}
      onOk={handleBuy}
      onCancel={handleCancel}
      okText="購入"
      cancelText="キャンセル"
      confirmLoading={buyMutation.isPending}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          quantity: 100,
        }}
      >
        <Form.Item
          label="銘柄"
          name="symbol"
          rules={[{ required: true, message: '銘柄を選択してください' }]}
        >
          <Select
            showSearch
            placeholder="銘柄コードまたは銘柄名で検索"
            onSearch={setSearchQuery}
            filterOption={false}
            loading={isLoadingCompanies}
            notFoundContent={
              searchQuery.length > 0
                ? '該当する銘柄が見つかりません'
                : '銘柄コードまたは銘柄名を入力してください'
            }
            options={companies?.map((company) => ({
              value: company.symbol,
              label: `${company.symbol} - ${company.name || '---'}`,
            }))}
          />
        </Form.Item>

        <Form.Item
          label="株数"
          name="quantity"
          rules={[
            { required: true, message: '株数を入力してください' },
            { type: 'number', min: 1, message: '1株以上を入力してください' },
          ]}
        >
          <Space.Compact style={{ width: '100%' }}>
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              step={100}
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value: string | undefined): number =>
                Number(value?.replace(/,/g, '') || 0)
              }
            />
            <Input style={{ width: 50 }} value="株" disabled />
          </Space.Compact>
        </Form.Item>

        <Form.Item
          label="購入価格（1株あたり）"
          name="price"
          help="未入力の場合は最新株価が使用されます"
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0.01}
            step={10}
            precision={2}
            formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={(value: string | undefined): number =>
              Number(value?.replace(/¥\s?|,/g, '') || 0)
            }
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
            placeholder="例: 配当狙いで購入"
            maxLength={500}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default BuyModal
