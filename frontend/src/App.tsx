import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './layout/AppLayout'
import { EquipmentPage } from './pages/EquipmentPage'
import { InventoryPage } from './pages/InventoryPage'
import { ProductionPage } from './pages/ProductionPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/equipment" replace />} />
        <Route path="equipment" element={<EquipmentPage />} />
        <Route path="production" element={<ProductionPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="work-orders" element={<WorkOrdersPage />} />
        <Route path="*" element={<Navigate to="/equipment" replace />} />
      </Route>
    </Routes>
  )
}
