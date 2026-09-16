export const machineStatusMap: Record<string, { text: string; color: string }> = {
  running: { text: '运行中', color: 'success' },
  idle: { text: '待机', color: 'processing' },
  maintenance: { text: '维护中', color: 'warning' },
  offline: { text: '离线', color: 'default' },
}

export const alarmLevelMap: Record<string, { text: string; color: string }> = {
  low: { text: '低', color: 'default' },
  medium: { text: '中', color: 'processing' },
  high: { text: '高', color: 'warning' },
  critical: { text: '严重', color: 'error' },
}

export const workOrderStatusMap: Record<string, { text: string; color: string }> = {
  pending: { text: '待处理', color: 'default' },
  in_progress: { text: '处理中', color: 'processing' },
  completed: { text: '已完成', color: 'success' },
  cancelled: { text: '已取消', color: 'error' },
}

export const workOrderPriorityMap: Record<string, { text: string; color: string }> = {
  low: { text: '低', color: 'default' },
  medium: { text: '中', color: 'processing' },
  high: { text: '高', color: 'warning' },
  urgent: { text: '紧急', color: 'error' },
}

export const workOrderTypeMap: Record<string, string> = {
  maintenance: '保养',
  repair: '维修',
  inspection: '巡检',
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false })
}

export function formatNumber(value: number | string) {
  return Number(value).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}
