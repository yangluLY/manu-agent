import type { EChartsOption } from 'echarts'

export function asEChartsOption(
  option: Record<string, unknown> | null,
): EChartsOption | undefined {
  return option ? (option as EChartsOption) : undefined
}

export function formatAnalyticsValue(value: unknown): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function withRowKeys(
  rows: Array<Record<string, unknown>>,
): Array<Record<string, unknown>> {
  return rows.map((row, index) => ({
    ...row,
    __rowKey: index,
  }))
}
