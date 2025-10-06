import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Analysis from './pages/Analysis'
import Candidates from './pages/Candidates'
import Dashboard from './pages/Dashboard'
import StockDetail from './pages/StockDetail'
import StockList from './pages/StockList'

// React Query設定
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <ConfigProvider locale={jaJP}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stocks" element={<StockList />} />
              <Route path="/stocks/:symbol" element={<StockDetail />} />
              <Route path="/candidates" element={<Candidates />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/analysis/:symbol" element={<Analysis />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  )
}

export default App
