export interface BIQueryResultData {
  columns: string[]
  rows: Array<Record<string, unknown>>
  row_count: number
  execution_time_ms: number
  truncated: boolean
}

export interface BIAnalysis {
  summary: string
  key_findings: string[]
  recommendations: string[]
  limitations: string[]
}

export type BIChartType = 'bar' | 'line' | 'pie' | 'table'

export interface BIChartSpec {
  type: BIChartType
  title: string
  x_field: string | null
  y_fields: string[]
  category_field: string | null
  value_field: string | null
  series: Array<{ name: string; field: string }>
  data: Array<Record<string, unknown>>
  reason: string | null
}

export interface BIPipelineResult {
  question: string
  sql: string
  data: BIQueryResultData
  analysis: BIAnalysis
  chart: BIChartSpec
  echarts_option: Record<string, unknown> | null
  attempts: Array<{
    attempt: number
    sql: string
    error: string | null
    corrected: boolean
  }>
  retry_count: number
}
