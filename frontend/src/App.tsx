
import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { AppLayout } from './layout/AppLayout'

import { EquipmentPage } from './pages/EquipmentPage'
import { InventoryPage } from './pages/InventoryPage'
import { ProductionPage } from './pages/ProductionPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'
import { ChatPage } from './pages/ChatPage'
import { ConversationHistoryPage } from './pages/ConversationHistoryPage'
import { BIPage } from './pages/BIPage'

import WorkflowChat from './pages/WorkflowChat'
import Login from './pages/Login'

import {
  AuthProvider,
  useAuth,
} from './context/AuthContext'

import { ProtectedRoute } from './components/ProtectedRoute'


function LoginRoute() {
  const { accessToken } = useAuth()

  if (accessToken) {
    return <Navigate to="/equipment" replace />
  }

  return <Login />
}


function AppRoutes() {
  return (
    <Routes>
      {/* 公共登录页面 */}
      <Route
        path="/login"
        element={<LoginRoute />}
      />

      {/* 需要登录才能访问的页面 */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route
            index
            element={<Navigate to="/equipment" replace />}
          />

          <Route
            path="equipment"
            element={<EquipmentPage />}
          />

          <Route
            path="production"
            element={<ProductionPage />}
          />

          <Route
            path="inventory"
            element={<InventoryPage />}
          />

          <Route
            path="work-orders"
            element={<WorkOrdersPage />}
          />

          <Route
            path="chat"
            element={<ChatPage />}
          />

          <Route
            path="chat/:conversationId"
            element={<ChatPage />}
          />

          <Route
            path="conversations"
            element={<ConversationHistoryPage />}
          />

          <Route
            path="bi"
            element={<BIPage />}
          />

          <Route
            path="workflow"
            element={<WorkflowChat />}
          />

          <Route
            path="*"
            element={<Navigate to="/equipment" replace />}
          />
        </Route>
      </Route>
    </Routes>
  )
}


export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
