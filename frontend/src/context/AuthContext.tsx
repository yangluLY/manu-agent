
import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
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
const TOKEN_STORAGE_KEY = 'manu-agent.access-token'

function readStoredToken(): string {
  try {
    return window.sessionStorage.getItem(TOKEN_STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

function storeToken(token: string) {
  try {
    if (token) {
      window.sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
    } else {
      window.sessionStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  } catch {
    // 浏览器禁用存储时，仍允许当前页面使用内存中的登录状态。
  }
}

export function AuthProvider({
  children,
}: {
  children: ReactNode
}) {
  // 首次渲染时恢复，避免受保护路由在刷新时误判为未登录。
  const [accessToken, setAccessToken] = useState(readStoredToken)

  const login = useCallback((token: string) => {
    if (!token.trim()) {
      throw new Error('无效的 Access Token')
    }

    storeToken(token)
    setAccessToken(token)
  }, [])

  const logout = useCallback(() => {
    storeToken('')
    setAccessToken('')
  }, [])

  useLayoutEffect(() => {
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
