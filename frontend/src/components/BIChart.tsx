import { BarChartOutlined, DatabaseOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { Card, Space, Tag, Typography } from 'antd'
import type { BIPipelineResult } from '../types/analytics'
import { asEChartsOption } from '../utils/chart'
import { BIDataTable } from './BIDataTable'

interface BIChartProps {
  result: BIPipelineResult
}

export function BIChart({ result }: BIChartProps) {
  const option = asEChartsOption(result.echarts_option)

  return (
    <Card
      size="small"
      className="section-card"
      title={result.chart.title}
      extra={
        <Space>
          <Tag icon={<BarChartOutlined />} color="blue">
            {result.chart.type}
          </Tag>
          <Tag icon={<DatabaseOutlined />}>{result.data.row_count} 行</Tag>
          <Tag>{result.data.execution_time_ms} ms</Tag>
        </Space>
      }
    >
      {option ? (
        <ReactECharts option={option} notMerge style={{ height: 420 }} />
      ) : (
        <BIDataTable data={result.data} paginated={false} />
      )}
      {result.chart.reason ? (
        <Typography.Text type="secondary">图表选择：{result.chart.reason}</Typography.Text>
      ) : null}
    </Card>
  )
}
