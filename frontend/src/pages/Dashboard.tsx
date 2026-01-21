import {
  AimOutlined,
  CalendarOutlined,
  DollarOutlined,
  LineChartOutlined,
  RiseOutlined,
  StarOutlined,
  StockOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Button, Card, Col, Row, Spin, Statistic, Typography } from 'antd'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { analysisApi, candidatesApi, portfolioApi } from '../services/api'
import type { DashboardPortfolioSummary } from '../types/portfolio'
import type { CandidatesCount, SystemStats } from '../types/stock'

const { Title } = Typography

const Dashboard = () => {
  const navigate = useNavigate()
  const { user } = useAuth()

  // システム統計取得（プライム市場）
  const { data: systemStats, isLoading: statsLoading } = useQuery<SystemStats>({
    queryKey: ['systemStats'],
    queryFn: analysisApi.getSystemStats,
  })

  // 投資候補統計取得
  const { data: candidatesCount, isLoading: candidatesLoading } =
    useQuery<CandidatesCount>({
      queryKey: ['candidatesCount'],
      queryFn: candidatesApi.getCandidatesCount,
    })

  // ポートフォリオ概要取得（ログイン時のみ）
  const { data: portfolioSummary, isLoading: portfolioLoading } =
    useQuery<DashboardPortfolioSummary>({
      queryKey: ['portfolioSummary'],
      queryFn: portfolioApi.getPortfolioSummary,
      enabled: !!user,
    })

  if (statsLoading || candidatesLoading || (user && portfolioLoading)) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  // 投資候補カードクリック時のハンドラ
  const handleCandidatesClick = () => {
    navigate('/candidates?market=prime&minDividend=3&maxDivergence=-5')
  }

  // 高スコアカードクリック時のハンドラ
  const handleHighScoreClick = () => {
    navigate('/candidates?market=prime&minScore=5')
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 24 }}>
        ダッシュボード
      </Title>

      {/* 投資候補情報セクション */}
      <Title level={4} style={{ marginBottom: 16 }}>
        投資候補情報（プライム市場）
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            onClick={handleCandidatesClick}
            style={{ cursor: 'pointer', borderColor: '#1890ff' }}
          >
            <Statistic
              title="投資候補"
              value={candidatesCount?.total_candidates || 0}
              prefix={<AimOutlined />}
              suffix={
                <span>
                  銘柄 <RiseOutlined style={{ fontSize: 12 }} />
                </span>
              }
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card
            hoverable
            onClick={handleHighScoreClick}
            style={{ cursor: 'pointer', borderColor: '#1890ff' }}
          >
            <Statistic
              title="高スコア候補"
              value={candidatesCount?.high_score || 0}
              prefix={<StarOutlined />}
              suffix={
                <span>
                  銘柄 <RiseOutlined style={{ fontSize: 12 }} />
                </span>
              }
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* データ更新状況セクション */}
      <Title level={4} style={{ marginBottom: 16 }}>
        データ更新状況
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="最終更新日"
              value={
                systemStats?.latest_price_date
                  ? new Date(systemStats.latest_price_date).toLocaleDateString(
                      'ja-JP',
                    )
                  : '未更新'
              }
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="株価データ"
              value={systemStats?.symbols_with_prices || 0}
              prefix={<LineChartOutlined />}
              suffix="銘柄"
            />
          </Card>
        </Col>
      </Row>

      {/* ポートフォリオ概要セクション（ログイン時のみ表示） */}
      {user && (
        <>
          <Title level={4} style={{ marginBottom: 16 }}>
            ポートフォリオ概要
          </Title>
          <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
            {portfolioSummary?.has_portfolio ? (
              <>
                <Col xs={24} sm={8} lg={6}>
                  <Card>
                    <Statistic
                      title="保有銘柄数"
                      value={portfolioSummary.positions_count}
                      prefix={<StockOutlined />}
                      suffix="銘柄"
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={8} lg={6}>
                  <Card>
                    <Statistic
                      title="総損益"
                      value={portfolioSummary.total_profit_loss}
                      prefix={<DollarOutlined />}
                      suffix="円"
                      precision={0}
                      valueStyle={{
                        color:
                          portfolioSummary.total_profit_loss >= 0
                            ? '#3f8600'
                            : '#cf1322',
                      }}
                      formatter={(value) =>
                        `${Number(value) >= 0 ? '+' : ''}${Number(value).toLocaleString()}`
                      }
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={8} lg={6}>
                  <Card>
                    <Statistic
                      title="損益率"
                      value={portfolioSummary.total_profit_loss_rate}
                      prefix={<RiseOutlined />}
                      suffix="%"
                      precision={2}
                      valueStyle={{
                        color:
                          portfolioSummary.total_profit_loss_rate >= 0
                            ? '#3f8600'
                            : '#cf1322',
                      }}
                      formatter={(value) =>
                        `${Number(value) >= 0 ? '+' : ''}${Number(value).toFixed(2)}`
                      }
                    />
                  </Card>
                </Col>
              </>
            ) : (
              <Col xs={24} sm={12} lg={8}>
                <Card>
                  <p style={{ marginBottom: 16, color: '#8c8c8c' }}>
                    ポートフォリオがまだありません
                  </p>
                  <Link to="/portfolio">
                    <Button type="primary">ポートフォリオを作成</Button>
                  </Link>
                </Card>
              </Col>
            )}
          </Row>
        </>
      )}

      {/* クイックアクション */}
      <Title level={4} style={{ marginBottom: 16 }}>
        クイックアクション
      </Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <Card.Meta
              title="投資候補を見る"
              description="AI分析による投資候補銘柄をチェック"
            />
            <Link to="/candidates">
              <Button type="primary" block style={{ marginTop: 16 }}>
                候補を見る
              </Button>
            </Link>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <Card.Meta
              title="銘柄検索"
              description="個別銘柄の詳細情報を確認"
            />
            <Link to="/stocks">
              <Button type="primary" block style={{ marginTop: 16 }}>
                銘柄を検索
              </Button>
            </Link>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <Card.Meta
              title="市場分析"
              description="技術分析とトレンドを分析"
            />
            <Link to="/analysis">
              <Button type="primary" block style={{ marginTop: 16 }}>
                分析を見る
              </Button>
            </Link>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
