
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  setAccessTokenGetter,
  setUnauthorizedHandler,
} from '../api/client'

interface AuthContextType {
  accessToken: string
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({
  children,
}: {
  children: ReactNode
}) {
  const [accessToken, setAccessToken] = useState('')

  const login = useCallback((token: string) => {
    if (!token.trim()) {
      throw new Error('无效的 Access Token')
    }

    setAccessToken(token)
  }, [])

  const logout = useCallback(() => {
    setAccessToken('')
  }, [])

  useEffect(() => {
    // 为 Axios 注入当前 Token
    setAccessTokenGetter(() => accessToken || null)

    // 后端返回 401 时清空登录状态
    setUnauthorizedHandler(logout)

    return () => {
      setAccessTokenGetter(() => null)
      setUnauthorizedHandler(null)
    }
  }, [accessToken, logout])

  return (
    <AuthContext.Provider
      value={{
        accessToken,
        isAuthenticated: Boolean(accessToken),
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth 必须在 AuthProvider 内部调用',
    )
  }

  return context
}
