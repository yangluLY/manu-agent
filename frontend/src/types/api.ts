export type MachineStatus = 'running' | 'idle' | 'maintenance' | 'offline' | string
export type AlarmLevel = 'low' | 'medium' | 'high' | 'critical'
export type WorkOrderType = 'maintenance' | 'repair' | 'inspection'
export type WorkOrderPriority = 'low' | 'medium' | 'high' | 'urgent'
export type WorkOrderStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled'

export interface Machine {
  id: number
  code: string
  name: string
  model: string | null
  line_code: string | null
  status: MachineStatus
  last_heartbeat_at: string | null
  created_at: string
  updated_at: string
}

export interface Alarm {
  id: number
  machine_id: number
  alarm_code: string
  alarm_message: string
  level: AlarmLevel
  started_at: string
  ended_at: string | null
}

export interface ProductionRecord {
  id: number
  machine_id: number
  line_code: string
  product_code: string
  planned_qty: number
  actual_qty: number
  defect_qty: number
  production_date: string
  created_at: string
}

export interface ProductionSummary {
  record_count: number
  planned_qty: number
  actual_qty: number
  defect_qty: number
  completion_rate: number
  defect_rate: number
}

export interface Material {
  id: number
  code: string
  name: string
  unit: string
  stock_qty: number | string
  safe_stock: number | string
}

export interface WorkOrder {
  id: number
  order_no: string
  machine_id: number
  type: WorkOrderType
  priority: WorkOrderPriority
  description: string
  status: WorkOrderStatus
  assigned_to: string | null
  created_at: string
  updated_at: string
}

export interface ProductionQuery {
  machine_id?: number
  line_code?: string
  product_code?: string
  start_date?: string
  end_date?: string
}

export interface CreateWorkOrderPayload {
  machine_id: number
  type: WorkOrderType
  priority: WorkOrderPriority
  description: string
  assigned_to?: string
}

export type UpdateWorkOrderPayload = Partial<
  Pick<WorkOrder, 'type' | 'priority' | 'description' | 'status' | 'assigned_to'>
>
