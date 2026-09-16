import { ReloadOutlined, RightOutlined } from '@ant-design/icons'
import { Button, Card, Col, Input, Row, Select, Space, Statistic, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { PageTitle } from '../components/PageTitle'
import { RequestError } from '../components/RequestError'
import { StatusTag } from '../components/StatusTag'
import { useSelection } from '../context/SelectionContext'
import { getErrorMessage, mesApi } from '../services/api'
import type { Machine } from '../types/api'
import { formatDateTime, machineStatusMap } from '../utils/format'

export function EquipmentPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { lineCode, machineId, selectLine, selectMachine } = useSelection()
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<string>()
  const [lineFilter, setLineFilter] = useState<string | undefined>(
    searchParams.get('line_code') || lineCode,
  )

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setMachines(await mesApi.getMachines())
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const target = searchParams.get('view') === 'machines' ? 'machine-section' : 'line-section'
    document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [searchParams])

  const lines = useMemo(() => {
    const groups = new Map<string, Machine[]>()
    machines.forEach((machine) => {
      const code = machine.line_code || '未分配产线'
      groups.set(code, [...(groups.get(code) || []), machine])
    })
    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))
  }, [machines])

  const filteredMachines = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase()
    return machines.filter((machine) => {
      const matchesLine = !lineFilter || (machine.line_code || '未分配产线') === lineFilter
      const matchesStatus = !status || machine.status === status
      const matchesKeyword =
        !lowerKeyword ||
        [machine.code, machine.name, machine.model].some((value) =>
          value?.toLowerCase().includes(lowerKeyword),
        )
      return matchesLine && matchesStatus && matchesKeyword
    })
  }, [keyword, lineFilter, machines, status])

  const chooseLine = (code?: string) => {
    setLineFilter(code)
    selectLine(code)
    const next = new URLSearchParams(searchParams)
    if (code) next.set('line_code', code)
    else next.delete('line_code')
    next.delete('machine_id')
    setSearchParams(next, { replace: true })
  }

  const openMachine = (machine: Machine) => {
    selectMachine(machine.id, machine.line_code || undefined)
    navigate(
      `/production?view=alarms&machine_id=${machine.id}${machine.line_code ? `&line_code=${machine.line_code}` : ''}`,
    )
  }

  const columns: ColumnsType<Machine> = [
    {
      title: '设备',
      key: 'machine',
      render: (_, machine) => (
        <div>
          <strong>{machine.code}</strong>
          <div className="secondary-text">{machine.name}</div>
        </div>
      ),
    },
    { title: '型号', dataIndex: 'model', key: 'model', render: (value) => value || '—' },
    { title: '产线', dataIndex: 'line_code', key: 'line_code', render: (value) => value || '未分配' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => <StatusTag value={value} map={machineStatusMap} />,
    },
    {
      title: '最后心跳',
      dataIndex: 'last_heartbeat_at',
      key: 'last_heartbeat_at',
      render: (value: string | null) => formatDateTime(value),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, machine) => (
        <Button
          type="link"
          onClick={(event) => {
            event.stopPropagation()
            openMachine(machine)
          }}
        >
          报警与生产 <RightOutlined />
        </Button>
      ),
    },
  ]

  const abnormalCount = machines.filter((item) => !['running', 'idle'].includes(item.status)).length

  return (
    <div>
      <PageTitle
        title="产线与设备"
        description="先选择产线，再进入设备的报警和生产数据。所有数据来自 FastAPI。"
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>
            刷新
          </Button>
        }
      />

      {error ? <RequestError message={error} onRetry={() => void load()} /> : null}

      <Row gutter={[12, 12]} className="summary-row">
        <Col xs={12} lg={6}>
          <Card size="small"><Statistic title="产线数" value={lines.length} /></Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card size="small"><Statistic title="设备总数" value={machines.length} /></Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card size="small"><Statistic title="运行中" value={machines.filter((item) => item.status === 'running').length} valueStyle={{ color: '#389e0d' }} /></Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card size="small"><Statistic title="异常 / 维护" value={abnormalCount} valueStyle={{ color: abnormalCount ? '#d46b08' : undefined }} /></Card>
        </Col>
      </Row>

      <Card id="line-section" title="产线" size="small" className="section-card" loading={loading}>
        <div className="line-grid">
          {lines.map(([code, lineMachines]) => {
            const running = lineMachines.filter((item) => item.status === 'running').length
            const selected = lineFilter === code
            return (
              <button
                type="button"
                key={code}
                className={`line-card${selected ? ' selected' : ''}`}
                onClick={() => chooseLine(code)}
              >
                <span>
                  <strong>{code}</strong>
                  <small>{lineMachines.length} 台设备</small>
                </span>
                <Tag color={running === lineMachines.length ? 'success' : 'warning'}>
                  运行 {running}/{lineMachines.length}
                </Tag>
              </button>
            )
          })}
        </div>
      </Card>

      <Card id="machine-section" title="设备列表" size="small" className="section-card">
        <Space wrap className="filter-bar">
          <Input.Search
            allowClear
            placeholder="搜索设备编码、名称或型号"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            style={{ width: 260 }}
          />
          <Select
            allowClear
            placeholder="全部产线"
            value={lineFilter}
            onChange={chooseLine}
            options={lines.map(([code]) => ({ label: code, value: code }))}
            style={{ width: 150 }}
          />
          <Select
            allowClear
            placeholder="全部状态"
            value={status}
            onChange={setStatus}
            options={Object.entries(machineStatusMap).map(([value, item]) => ({
              label: item.text,
              value,
            }))}
            style={{ width: 140 }}
          />
        </Space>
        <Table<Machine>
          rowKey="id"
          size="middle"
          loading={loading}
          columns={columns}
          dataSource={filteredMachines}
          scroll={{ x: 900 }}
          rowClassName={(machine) => (machine.id === machineId ? 'selected-row' : '')}
          onRow={(machine) => ({ onDoubleClick: () => openMachine(machine) })}
          pagination={{
            defaultPageSize: 5,
            showSizeChanger: true,
            pageSizeOptions: [5, 10, 20],
            showTotal: (total) => `共 ${total} 台设备`,
          }}
        />
      </Card>
    </div>
  )
}
