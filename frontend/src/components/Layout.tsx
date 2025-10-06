import { Link, useLocation } from 'react-router-dom'

interface LayoutProps {
  children: React.ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation()

  const navItems = [
    { path: '/', label: '🏠 ダッシュボード' },
    { path: '/stocks', label: '📊 銘柄一覧' },
    { path: '/candidates', label: '🎯 投資候補' },
    { path: '/analysis', label: '📈 分析' },
  ]

  return (
    <div className="flex min-h-screen bg-gray-900">
      <nav className="w-64 bg-gray-900 text-white shadow-lg">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-xl font-semibold">📈 株式分析システム</h1>
        </div>
        <ul className="space-y-0">
          {navItems.map((item) => (
            <li key={item.path} className="border-b border-gray-700">
              <Link
                to={item.path}
                className={`block px-6 py-4 font-medium transition-colors duration-200 ${
                  location.pathname === item.path
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
      <main className="flex-1 p-8 bg-gray-900 text-gray-100 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}

export default Layout
