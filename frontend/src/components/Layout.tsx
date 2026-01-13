import { CloseOutlined, MenuOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { Button, Dropdown, message } from 'antd'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface LayoutProps {
  children: React.ReactNode
}

/** ヘッダーの高さ（px） */
const HEADER_HEIGHT = 64

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  /**
   * ナビゲーションアイテムがアクティブかどうかを判定する
   */
  const isNavItemActive = (path: string): boolean => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname === path || location.pathname.startsWith(path)
  }

  const navItems = [
    { path: '/', label: '🏠 ダッシュボード' },
    { path: '/stocks', label: '📊 銘柄一覧' },
    { path: '/candidates', label: '🎯 投資候補' },
    { path: '/analysis', label: '📈 分析' },
  ]

  // ログイン済みの場合はポートフォリオメニューを表示
  if (user) {
    navItems.push({ path: '/portfolio', label: '💼 ポートフォリオ' })
  }

  // 管理者の場合のみ管理メニューを表示
  if (user?.role === 'admin') {
    navItems.push({ path: '/admin', label: '⚙️ 管理' })
  }

  const handleLogout = async () => {
    try {
      await logout()
      message.success('Logged out')
      navigate('/login')
    } catch {
      message.error('Logout failed')
    }
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'mypage',
      label: 'マイページ',
      onClick: () => navigate('/mypage'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      label: 'ログアウト',
      onClick: handleLogout,
    },
  ]

  return (
    <div className="flex flex-col min-h-screen bg-gray-900">
      {/* 共通ヘッダー */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-lg">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            {/* ハンバーガーメニュー（モバイルのみ表示） */}
            <Button
              type="text"
              icon={isSidebarOpen ? <CloseOutlined /> : <MenuOutlined />}
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="md:hidden text-white text-xl"
              aria-label={isSidebarOpen ? 'メニューを閉じる' : 'メニューを開く'}
              aria-expanded={isSidebarOpen}
              aria-controls="sidebar-nav"
            />
            <h1 className="text-xl font-semibold text-white">
              📈 株式分析システム
            </h1>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                trigger={['click']}
              >
                <Button type="text" className="text-gray-300 hover:text-white">
                  <div className="flex items-center gap-2">
                    <span>{user.display_name}</span>
                    {user.role === 'admin' && (
                      <span className="text-xs bg-blue-600 px-1.5 py-0.5 rounded">
                        管理者
                      </span>
                    )}
                  </div>
                </Button>
              </Dropdown>
            ) : (
              <Button type="primary" onClick={() => navigate('/login')}>
                ログイン
              </Button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 relative">
        {/* オーバーレイ（モバイルでサイドバー開いている時のみ表示） */}
        {isSidebarOpen && (
          <button
            type="button"
            className="fixed inset-0 bg-black/30 z-40 md:hidden border-none cursor-pointer"
            onClick={() => setIsSidebarOpen(false)}
            aria-label="メニューを閉じる"
          />
        )}

        {/* サイドナビゲーション */}
        {/* biome-ignore lint/correctness/useUniqueElementIds: Layoutはシングルトンコンポーネントのため静的IDで問題なし */}
        <nav
          id="sidebar-nav"
          className={`
            w-64 bg-gray-900 text-white shadow-lg
            fixed md:static inset-y-0 left-0 z-50
            transform transition-transform duration-300
            ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          `}
          style={{ top: `${HEADER_HEIGHT}px` }}
        >
          <ul className="space-y-0">
            {navItems.map((item) => (
              <li key={item.path} className="border-b border-gray-700">
                <Link
                  to={item.path}
                  onClick={() => setIsSidebarOpen(false)}
                  className={`block px-6 py-4 font-medium transition-colors duration-200 ${
                    isNavItemActive(item.path)
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* メインコンテンツ */}
        <main className="flex-1 p-4 md:p-8 bg-gray-900 text-gray-100 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout
