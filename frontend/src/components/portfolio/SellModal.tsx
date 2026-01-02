import { useMutation, useQueryClient } from '@tanstack/react-query'
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
import { portfolioApi } from '../../services/api'
import type { PositionDetail, SellRequest } from '../../types/portfolio'

interface SellModalProps {
  visible: boolean
  portfolioId: number
  positions: PositionDetail[]
  onCancel: () => void
}

const SellModal = ({ visible, portfolioId, positions, onCancel }: SellModalProps) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const selectedSymbol = Form.useWatch('symbol', form)

  // 選択された銘柄の保有株数を取得
  const selectedPosition = positions.find((p) => p.symbol === selectedSymbol)
  const maxQuantity = selectedPosition?.quantity || 0

  // 売却Mutation
  const sellMutation = useMutation({
    mutationFn: (data: SellRequest) => portfolioApi.sellStock(portfolioId, data),
    onSuccess: () => {
      message.success('銘柄を売却しました')
      queryClient.invalidateQueries({ queryKey: ['portfolio', portfolioId.toString()] })
      queryClient.invalidateQueries({ queryKey: ['portfolios'] })
      form.resetFields()
      onCancel()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '銘柄の売却に失敗しました')
    },
  })

  // 売却実行
  const handleSell = () => {
    form.validateFields().then((values) => {
      const sellRequest: SellRequest = {
        symbol: values.symbol,
        quantity: values.quantity,
        price: values.price || null,
        transaction_date: values.transaction_date
          ? values.transaction_date.toISOString()
          : null,
        notes: values.notes || null,
      }
      sellMutation.mutate(sellRequest)
    })
  }

  // モーダルキャンセル
  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  return (
    <Modal
      title="銘柄を売却"
      open={visible}
      onOk={handleSell}
      onCancel={handleCancel}
      okText="売却"
      cancelText="キャンセル"
      confirmLoading={sellMutation.isPending}
      width={600}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          label="銘柄"
          name="symbol"
          rules={[{ required: true, message: '銘柄を選択してください' }]}
        >
          <Select
            placeholder="売却する銘柄を選択"
            options={positions.map((position) => ({
              value: position.symbol,
              label: `${position.symbol} - ${position.company_name || '---'} (保有: ${position.quantity.toLocaleString()}株)`,
            }))}
            onChange={() => {
              // 銘柄変更時に株数をリセット
              form.setFieldValue('quantity', undefined)
            }}
          />
        </Form.Item>

        {selectedPosition && (
          <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#8c8c8c' }}>保有株数</span>
              <span style={{ fontWeight: 500 }}>{selectedPosition.quantity.toLocaleString()}株</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#8c8c8c' }}>平均取得単価</span>
              <span style={{ fontWeight: 500 }}>¥{selectedPosition.average_price.toLocaleString()}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8c8c8c' }}>現在株価</span>
              <span style={{ fontWeight: 500 }}>
                {selectedPosition.current_price !== null
                  ? `¥${selectedPosition.current_price.toLocaleString()}`
                  : '---'}
              </span>
            </div>
          </div>
        )}

        <Form.Item
          label="売却株数"
          name="quantity"
          rules={[
            { required: true, message: '売却株数を入力してください' },
            { type: 'number', min: 1, message: '1株以上を入力してください' },
            {
              type: 'number',
              max: maxQuantity,
              message: `保有株数（${maxQuantity.toLocaleString()}株）を超えています`,
            },
          ]}
        >
          <Space.Compact style={{ width: '100%' }}>
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              max={maxQuantity}
              step={100}
              disabled={!selectedSymbol}
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value: string | undefined): number =>
                Number(value?.replace(/,/g, '') || 0)
              }
            />
            <Input
              style={{ width: 150 }}
              value={`株 / ${maxQuantity.toLocaleString()}株`}
              disabled
            />
          </Space.Compact>
        </Form.Item>

        <Form.Item
          label="売却価格（1株あたり）"
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
            placeholder="例: 利確のため売却"
            maxLength={500}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default SellModal
