import axios, { AxiosError } from 'axios'
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

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 12_000,
  headers: { Accept: 'application/json' },
})

interface ApiErrorBody {
  detail?: string | Array<{ loc?: Array<string | number>; msg?: string }>
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>
    const detail = axiosError.response?.data?.detail

    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) => `${item.loc?.slice(1).join('.') || '请求参数'}：${item.msg || '格式错误'}`)
        .join('；')
    }
    if (axiosError.code === 'ECONNABORTED') return '请求超时，请检查 FastAPI 服务状态'
    if (!axiosError.response) return '无法连接 FastAPI，请确认后端已在 8000 端口启动'
    return `请求失败（HTTP ${axiosError.response.status}）`
  }

  return error instanceof Error ? error.message : '发生未知错误'
}

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
