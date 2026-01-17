import { ReloadOutlined } from '@ant-design/icons'
import { Button, Modal, Spin, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { aiAnalysisApi } from '../../services/api'
import type { AIAnalysis } from '../../types/stock'

const { Paragraph, Text, Title } = Typography

interface AIAnalysisModalProps {
  visible: boolean
  symbol: string
  onClose: () => void
}

const AIAnalysisModal = ({ visible, symbol, onClose }: AIAnalysisModalProps) => {
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [polling, setPolling] = useState(false)

  // 分析を開始する
  const startAnalysis = async () => {
    setLoading(true)
    setAnalysis(null)
    try {
      const result = await aiAnalysisApi.startAnalysis(symbol)
      setAnalysis(result)

      // pending状態の場合、ポーリングを開始
      if (result.status === 'pending') {
        setPolling(true)
      }
    } catch (error) {
      console.error('AI分析の開始に失敗しました:', error)
    } finally {
      setLoading(false)
    }
  }

  // ポーリング処理
  useEffect(() => {
    if (!polling || !analysis) return

    const interval = setInterval(async () => {
      try {
        const updated = await aiAnalysisApi.getAnalysis(analysis.id)
        setAnalysis(updated)

        // completed または failed になったらポーリング終了
        if (updated.status === 'completed' || updated.status === 'failed') {
          setPolling(false)
        }
      } catch (error) {
        console.error('分析結果の取得に失敗しました:', error)
        setPolling(false)
      }
    }, 3000) // 3秒ごとにポーリング

    return () => clearInterval(interval)
  }, [polling, analysis])

  // モーダルを開いた時に最新の分析履歴を取得
  useEffect(() => {
    if (!visible) {
      setAnalysis(null)
      setPolling(false)
      return
    }

    const fetchLatestAnalysis = async () => {
      setLoading(true)
      try {
        const history = await aiAnalysisApi.getAnalysisHistory(symbol, 1)
        if (history.analyses.length > 0) {
          const latest = history.analyses[0]
          setAnalysis(latest)

          // pending状態の場合、ポーリングを開始
          if (latest.status === 'pending') {
            setPolling(true)
          }
        } else {
          // 履歴がない場合は自動的に分析を開始
          await startAnalysis()
        }
      } catch (error) {
        console.error('分析履歴の取得に失敗しました:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchLatestAnalysis()
  }, [visible, symbol])

  // 分析結果の表示内容を生成
  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <Paragraph style={{ marginTop: 16 }}>
            AI分析を準備しています...
          </Paragraph>
        </div>
      )
    }

    if (!analysis) {
      return (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Paragraph>分析データがありません</Paragraph>
          <Button type="primary" onClick={startAnalysis}>
            AI分析を開始
          </Button>
        </div>
      )
    }

    if (analysis.status === 'pending' || polling) {
      return (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <Paragraph style={{ marginTop: 16 }}>
            AI分析中です。しばらくお待ちください...
          </Paragraph>
          <Text type="secondary">
            分析開始: {new Date(analysis.created_at).toLocaleString('ja-JP')}
          </Text>
        </div>
      )
    }

    if (analysis.status === 'failed') {
      return (
        <div style={{ padding: '20px' }}>
          <Title level={5} type="danger">
            エラー
          </Title>
          <Paragraph type="danger">
            {analysis.error_message || 'AI分析に失敗しました'}
          </Paragraph>
          <Button
            type="primary"
            danger
            icon={<ReloadOutlined />}
            onClick={startAnalysis}
          >
            再度分析する
          </Button>
        </div>
      )
    }

    // completed状態
    return (
      <div>
        <div
          style={{
            marginBottom: 16,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Text type="secondary">
            分析日時: {new Date(analysis.created_at).toLocaleString('ja-JP')}
          </Text>
          <Button
            icon={<ReloadOutlined />}
            onClick={startAnalysis}
            loading={loading}
          >
            再分析
          </Button>
        </div>
        <div
          style={{
            maxHeight: '60vh',
            overflowY: 'auto',
            padding: '16px',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.8,
          }}
        >
          {analysis.analysis_text}
        </div>
      </div>
    )
  }

  return (
    <Modal
      title={`AI分析結果: ${symbol}`}
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>
          閉じる
        </Button>,
      ]}
      width={800}
    >
      {renderContent()}
    </Modal>
  )
}

export default AIAnalysisModal
