import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { App as AntdApp, ConfigProvider, Spin, theme } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Admin from './pages/Admin'
import Analysis from './pages/Analysis'
import Candidates from './pages/Candidates'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import MyPage from './pages/MyPage'
import Portfolio from './pages/Portfolio'
import PortfolioDetail from './pages/PortfolioDetail'
import Register from './pages/Register'
import StockList from './pages/StockList'
import Transactions from './pages/Transactions'

// React Query設定
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分
      refetchOnWindowFocus: false,
    },
  },
})

// 認証が必要なルートをガードするコンポーネント
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <Spin size="large" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* 公開ルート（ログイン・登録画面） */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* 公開ルート（既存機能はログイン不要） */}
      <Route
        path="/*"
        element={
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stocks" element={<StockList />} />
              <Route path="/candidates" element={<Candidates />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/analysis/:symbol" element={<Analysis />} />
              {/* 認証必須ページ */}
              <Route
                path="/mypage"
                element={
                  <RequireAuth>
                    <MyPage />
                  </RequireAuth>
                }
              />
              <Route
                path="/portfolio"
                element={
                  <RequireAuth>
                    <Portfolio />
                  </RequireAuth>
                }
              />
              <Route
                path="/portfolio/:id"
                element={
                  <RequireAuth>
                    <PortfolioDetail />
                  </RequireAuth>
                }
              />
              <Route
                path="/portfolio/:id/transactions"
                element={
                  <RequireAuth>
                    <Transactions />
                  </RequireAuth>
                }
              />
              <Route
                path="/admin"
                element={
                  <RequireAuth>
                    <Admin />
                  </RequireAuth>
                }
              />
            </Routes>
          </Layout>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <ConfigProvider
      locale={jaJP}
      theme={{
        algorithm: theme.darkAlgorithm,
      }}
    >
      <AntdApp>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <AppRoutes />
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </AntdApp>
    </ConfigProvider>
  )
}

export default App
