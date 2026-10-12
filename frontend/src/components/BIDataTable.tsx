import { Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo } from 'react'
import type { BIQueryResultData } from '../types/analytics'
import { formatAnalyticsValue, withRowKeys } from '../utils/chart'

interface BIDataTableProps {
  data: BIQueryResultData
  paginated?: boolean
}

export function BIDataTable({ data, paginated = true }: BIDataTableProps) {
  const columns = useMemo<ColumnsType<Record<string, unknown>>>(
    () =>
      data.columns.map((column) => ({
        title: column,
        dataIndex: column,
        key: column,
        render: formatAnalyticsValue,
      })),
    [data.columns],
  )

  const rows = useMemo(() => withRowKeys(data.rows), [data.rows])

  return (
    <Table<Record<string, unknown>>
      size="small"
      rowKey="__rowKey"
      columns={columns}
      dataSource={rows}
      pagination={paginated ? { defaultPageSize: 10, hideOnSinglePage: true } : false}
      scroll={{ x: true }}
    />
  )
}
