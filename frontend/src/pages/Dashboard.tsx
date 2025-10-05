import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card, Col, Row, Statistic, Spin, Button } from 'antd'
import { ShopOutlined, LineChartOutlined, SearchOutlined, StarOutlined, CalendarOutlined, AimOutlined } from '@ant-design/icons'
import { analysisApi, candidatesApi } from '../services/api'
import type { SystemStats, CandidatesCount } from '../types/stock'

const Dashboard = () => {
  // システム統計取得
  const { data: systemStats, isLoading: statsLoading } = useQuery<SystemStats>({
    queryKey: ['systemStats'],
    queryFn: analysisApi.getSystemStats,
  })

  // 投資候補統計取得
  const { data: candidatesCount, isLoading: candidatesLoading } = useQuery<CandidatesCount>({
    queryKey: ['candidatesCount'],
    queryFn: candidatesApi.getCandidatesCount,
  })

  if (statsLoading || candidatesLoading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>📊 ダッシュボード</h1>

      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="企業データ"
              value={systemStats?.companies_count || 0}
              prefix={<ShopOutlined />}
              suffix="社"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="株価データ有り"
              value={systemStats?.symbols_with_prices || 0}
              prefix={<LineChartOutlined />}
              suffix="銘柄"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="分析済み銘柄"
              value={systemStats?.symbols_with_technical || 0}
              prefix={<SearchOutlined />}
              suffix="銘柄"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="投資候補"
              value={candidatesCount?.total_candidates || 0}
              prefix={<AimOutlined />}
              suffix="銘柄"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="高スコア候補"
              value={candidatesCount?.high_score || 0}
              prefix={<StarOutlined />}
              suffix="銘柄"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="最新更新日"
              value={systemStats?.latest_price_date ?
                new Date(systemStats.latest_price_date).toLocaleDateString('ja-JP') :
                '未更新'
              }
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <h2 style={{ marginBottom: 16 }}>🚀 クイックアクション</h2>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <Card.Meta
              title="🎯 投資候補を見る"
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
              title="📊 銘柄検索"
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
              title="📈 市場分析"
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