
import {
  Navigate,
  Outlet,
  useLocation,
} from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

/**
 * 路由权限保护组件
 *
 * 已登录：
 *   允许访问业务页面
 *
 * 未登录：
 *   跳转到 /login
 */
export function ProtectedRoute() {
  const { isAuthenticated } = useAuth()

  const location = useLocation()

  // 未登录：跳转登录页
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location,
        }}
      />
    )
  }

  // 已登录：渲染当前子路由
  return <Outlet />
}
