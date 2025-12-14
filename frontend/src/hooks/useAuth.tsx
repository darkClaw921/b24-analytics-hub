import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/auth'
import { api } from '../services/api'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is authenticated on mount
    const loadUser = async () => {
      if (authService.isAuthenticated()) {
        try {
          const response = await api.get<User>('/users/me')
          setUser(response.data)
        } catch (error: any) {
          // Логируем только в режиме разработки или если это не ошибка аутентификации
          if (import.meta.env.DEV || error.response?.status !== 401) {
            console.error('Error loading user:', error)
          }
          // Если токен невалиден, очищаем его
          if (error.response?.status === 401 || error.response?.status === 403) {
            authService.logout()
          }
        }
      }
      setLoading(false)
    }

    loadUser()
  }, [])

  const login = async (username: string, password: string) => {
    await authService.login(username, password)
    const response = await api.get<User>('/users/me')
    setUser(response.data)
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
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

