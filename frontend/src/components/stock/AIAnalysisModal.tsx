import { ReloadOutlined } from '@ant-design/icons'
import { Button, Modal, Spin, Typography, message } from 'antd'
import { useCallback, useEffect, useRef, useState } from 'react'
import Markdown, { type Components } from 'react-markdown'
import { aiAnalysisApi } from '../../services/api'
import type { AIAnalysis } from '../../types/stock'

const { Paragraph, Text, Title } = Typography

// ポーリング設定
const POLLING_INITIAL_INTERVAL_MS = 2000
const POLLING_MAX_INTERVAL_MS = 10000
const POLLING_BACKOFF_MULTIPLIER = 1.5

// Markdown要素にTailwindクラスを適用
const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-xl font-semibold text-blue-400 mt-6 mb-2 pb-2 border-b border-gray-600">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-semibold text-blue-400 mt-4 mb-2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold text-blue-400 mt-3 mb-1">{children}</h3>
  ),
  p: ({ children }) => <p className="my-2">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-6 my-2">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-6 my-2">{children}</ol>,
  li: ({ children }) => <li className="my-1">{children}</li>,
  strong: ({ children }) => (
    <strong className="font-semibold text-gray-100">{children}</strong>
  ),
  hr: () => <hr className="border-gray-600 my-4" />,
}

interface AIAnalysisModalProps {
  visible: boolean
  symbol: string
  onClose: () => void
}

// UTC時刻をJST（日本標準時）に変換して表示
const formatJST = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const AIAnalysisModal = ({ visible, symbol, onClose }: AIAnalysisModalProps) => {
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [polling, setPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef(POLLING_INITIAL_INTERVAL_MS)

  // 分析を開始する
  const startAnalysis = useCallback(async () => {
    setLoading(true)
    setAnalysis(null)
    setError(null)
    pollingIntervalRef.current = POLLING_INITIAL_INTERVAL_MS

    try {
      const result = await aiAnalysisApi.startAnalysis(symbol)
      setAnalysis(result)

      if (result.status === 'pending') {
        setPolling(true)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'AI分析の開始に失敗しました'
      setError(errorMessage)
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [symbol])

  // ポーリング処理（指数バックオフ）
  useEffect(() => {
    if (!polling || !analysis) return

    const poll = async () => {
      try {
        const updated = await aiAnalysisApi.getAnalysis(analysis.id)
        setAnalysis(updated)

        // completed または failed になったらポーリング終了
        if (updated.status === 'completed' || updated.status === 'failed') {
          setPolling(false)
          pollingIntervalRef.current = POLLING_INITIAL_INTERVAL_MS
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '分析結果の取得に失敗しました'
        setError(errorMessage)
        setPolling(false)
        pollingIntervalRef.current = POLLING_INITIAL_INTERVAL_MS
      }
    }

    const timeoutId = setTimeout(() => {
      poll()
      // 次回のポーリング間隔を増加（指数バックオフ）
      pollingIntervalRef.current = Math.min(
        pollingIntervalRef.current * POLLING_BACKOFF_MULTIPLIER,
        POLLING_MAX_INTERVAL_MS
      )
    }, pollingIntervalRef.current)

    return () => clearTimeout(timeoutId)
  }, [polling, analysis])

  // モーダルを開いた時に最新の分析履歴を取得
  useEffect(() => {
    if (!visible) {
      setAnalysis(null)
      setPolling(false)
      setError(null)
      pollingIntervalRef.current = POLLING_INITIAL_INTERVAL_MS
      return
    }

    const fetchLatestAnalysis = async () => {
      setLoading(true)
      setError(null)

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
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '分析履歴の取得に失敗しました'
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    fetchLatestAnalysis()
  }, [visible, symbol, startAnalysis])

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

    if (error && !analysis) {
      return (
        <div style={{ padding: '20px' }}>
          <Title level={5} type="danger">
            エラー
          </Title>
          <Paragraph type="danger">{error}</Paragraph>
          <Button
            type="primary"
            danger
            icon={<ReloadOutlined />}
            onClick={startAnalysis}
          >
            再試行
          </Button>
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
            分析開始: {formatJST(analysis.created_at)}
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
            分析日時: {formatJST(analysis.created_at)}
          </Text>
          <Button
            icon={<ReloadOutlined />}
            onClick={startAnalysis}
            loading={loading}
          >
            再分析
          </Button>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-4 bg-gray-800 rounded-lg leading-relaxed text-gray-200 border border-gray-600">
          <Markdown components={markdownComponents}>
            {analysis.analysis_text || ''}
          </Markdown>
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
