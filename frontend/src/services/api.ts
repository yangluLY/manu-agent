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
import type {
  AgentChatRequest,
  AgentChatResponse,
  AgentStreamEvent,
  AgentStreamHandlers,
} from '../types/chat'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 12_000,
  headers: { Accept: 'application/json' },
})

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function parseAgentStreamEvent(line: string): AgentStreamEvent {
  let parsed: unknown
  try {
    parsed = JSON.parse(line)
  } catch {
    throw new Error('Agent 返回了无法解析的流式数据')
  }

  if (!parsed || typeof parsed !== 'object' || !('type' in parsed)) {
    throw new Error('Agent 返回了无效的流式事件')
  }

  const event = parsed as Record<string, unknown>
  if (event.type === 'reset') return { type: 'reset' }
  if (event.type === 'status' && typeof event.message === 'string') {
    return { type: 'status', message: event.message }
  }
  if (event.type === 'delta' && typeof event.content === 'string') {
    return { type: 'delta', content: event.content }
  }
  if (event.type === 'done' && typeof event.answer === 'string') {
    return { type: 'done', answer: event.answer }
  }
  if (event.type === 'error' && typeof event.message === 'string') {
    return { type: 'error', message: event.message }
  }

  throw new Error('Agent 返回了未知或不完整的流式事件')
}

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

export const agentApi = {
  async chat(payload: AgentChatRequest): Promise<AgentChatResponse> {
    const { data } = await http.post<AgentChatResponse>('/api/v1/agent/chat', payload, {
      timeout: 120_000,
    })
    return data
  },

  async streamChat(
    payload: AgentChatRequest,
    handlers: AgentStreamHandlers,
    signal?: AbortSignal,
  ): Promise<void> {
    const response = await fetch(`${apiBaseUrl}/api/v1/agent/chat/stream`, {
      method: 'POST',
      headers: {
        Accept: 'application/x-ndjson',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal,
    })

    if (!response.ok) {
      let detail = `请求失败（HTTP ${response.status}）`
      try {
        const body = (await response.json()) as ApiErrorBody
        if (typeof body.detail === 'string') detail = body.detail
      } catch {
        // 响应不是 JSON 时保留 HTTP 状态信息。
      }
      throw new Error(detail)
    }

    if (!response.body) {
      throw new Error('浏览器未收到可读取的流式响应')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let completed = false

    const handleLine = (line: string) => {
      if (!line.trim()) return
      const event = parseAgentStreamEvent(line)

      switch (event.type) {
        case 'status':
          handlers.onStatus(event.message)
          break
        case 'delta':
          handlers.onDelta(event.content)
          break
        case 'reset':
          handlers.onReset()
          break
        case 'done':
          completed = true
          handlers.onDone(event.answer)
          break
        case 'error':
          throw new Error(event.message)
        default:
          throw new Error('Agent 返回了未知的流式事件')
      }
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        let newlineIndex = buffer.indexOf('\n')
        while (newlineIndex >= 0) {
          handleLine(buffer.slice(0, newlineIndex))
          buffer = buffer.slice(newlineIndex + 1)
          newlineIndex = buffer.indexOf('\n')
        }
      }
    } finally {
      reader.releaseLock()
    }

    buffer += decoder.decode()
    if (buffer.trim()) handleLine(buffer)
    if (!completed) throw new Error('Agent 流式响应意外中断')
  },
}
