import type {
  Alarm,
  CreateWorkOrderPayload,
  Machine,
  Material,
  ProductionQuery,
  ProductionRecord,
  ProductionSummary,
  UpdateWorkOrderPayload,
  WorkOrder,
} from '../types/api'
import { http } from './client'

export const mesApi = {
  async health(): Promise<{ status: string }> {
    const { data } = await http.get('/health')
    return data
  },

  async getMachines(): Promise<Machine[]> {
    const { data } = await http.get<Machine[]>('/api/v1/machines')
    return data
  },

  async getAlarms(activeOnly = false): Promise<Alarm[]> {
    const { data } = await http.get<Alarm[]>('/api/v1/alarms', {
      params: activeOnly ? { active_only: true } : undefined,
    })
    return data
  },

  async resolveAlarm(alarmId: number): Promise<Alarm> {
    const { data } = await http.patch<Alarm>(`/api/v1/alarms/${alarmId}/resolve`, {})
    return data
  },

  async getProductionRecords(params: ProductionQuery): Promise<ProductionRecord[]> {
    const { data } = await http.get<ProductionRecord[]>('/api/v1/production-records', { params })
    return data
  },

  async getProductionSummary(params: ProductionQuery): Promise<ProductionSummary> {
    const { data } = await http.get<ProductionSummary>('/api/v1/production-records/summary', {
      params,
    })
    return data
  },

  async getMaterials(): Promise<Material[]> {
    const { data } = await http.get<Material[]>('/api/v1/materials')
    return data
  },

  async getLowStockMaterials(): Promise<Material[]> {
    const { data } = await http.get<Material[]>('/api/v1/materials/low-stock')
    return data
  },

  async getWorkOrders(): Promise<WorkOrder[]> {
    const { data } = await http.get<WorkOrder[]>('/api/v1/work-orders')
    return data
  },

  async createWorkOrder(payload: CreateWorkOrderPayload): Promise<WorkOrder> {
    const { data } = await http.post<WorkOrder>('/api/v1/work-orders', payload)
    return data
  },

  async updateWorkOrder(id: number, payload: UpdateWorkOrderPayload): Promise<WorkOrder> {
    const { data } = await http.patch<WorkOrder>(`/api/v1/work-orders/${id}`, payload)
    return data
  },
}
