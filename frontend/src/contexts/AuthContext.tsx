import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { User } from '../types/auth'
import { authApi } from '../services/api'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (login_id: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = async () => {
    try {
      const authStatus = await authApi.me()
      setUser(authStatus.authenticated ? authStatus.user : null)
    } catch {
      setUser(null)
    }
  }

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const authStatus = await authApi.me()
        setUser(authStatus.authenticated ? authStatus.user : null)
      } catch {
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
    checkAuth()
  }, [])

  const login = async (login_id: string, password: string) => {
    const userData = await authApi.login({ login_id, password })
    setUser(userData)
  }

  const logout = async () => {
    await authApi.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
