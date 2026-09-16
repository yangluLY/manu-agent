import { CheckOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import {
  App as AntdApp,
  Button,
  Card,
  Col,
  DatePicker,
  Input,
  Popconfirm,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { Dayjs } from 'dayjs'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { PageTitle } from '../components/PageTitle'
import { RequestError } from '../components/RequestError'
import { StatusTag } from '../components/StatusTag'
import { useSelection } from '../context/SelectionContext'
import { getErrorMessage, mesApi } from '../services/api'
import type { Alarm, Machine, ProductionQuery, ProductionRecord, ProductionSummary } from '../types/api'
import { alarmLevelMap, formatDateTime, formatNumber } from '../utils/format'

const emptySummary: ProductionSummary = {
  record_count: 0,
  planned_qty: 0,
  actual_qty: 0,
  defect_qty: 0,
  completion_rate: 0,
  defect_rate: 0,
}

export function ProductionPage() {
  const { message } = AntdApp.useApp()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const selection = useSelection()
  const queryMachineId = Number(searchParams.get('machine_id')) || selection.machineId
  const queryLineCode = searchParams.get('line_code') || selection.lineCode

  const [machines, setMachines] = useState<Machine[]>([])
  const [records, setRecords] = useState<ProductionRecord[]>([])
  const [summary, setSummary] = useState<ProductionSummary>(emptySummary)
  const [alarms, setAlarms] = useState<Alarm[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [resolvingId, setResolvingId] = useState<number>()

  const [lineCode, setLineCode] = useState<string | undefined>(queryLineCode)
  const [machineId, setMachineId] = useState<number | undefined>(queryMachineId)
  const [productCode, setProductCode] = useState('')
  const [startDate, setStartDate] = useState<Dayjs | null>(null)
  const [endDate, setEndDate] = useState<Dayjs | null>(null)
  const [activeOnly, setActiveOnly] = useState(false)
  const [alarmLevel, setAlarmLevel] = useState<string>()
  const [appliedQuery, setAppliedQuery] = useState<ProductionQuery>(() => ({
    machine_id: queryMachineId,
    line_code: queryLineCode,
  }))

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [machineData, recordData, summaryData, alarmData] = await Promise.all([
        mesApi.getMachines(),
        mesApi.getProductionRecords(appliedQuery),
        mesApi.getProductionSummary(appliedQuery),
        mesApi.getAlarms(activeOnly),
      ])
      setMachines(machineData)
      setRecords(recordData)
      setSummary(summaryData)
      setAlarms(alarmData)
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [activeOnly, appliedQuery])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const target = searchParams.get('view') === 'alarms' ? 'alarm-section' : 'production-section'
    document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [searchParams])

  const lines = useMemo(
    () => [...new Set(machines.map((item) => item.line_code).filter(Boolean) as string[])].sort(),
    [machines],
  )

  const machineMap = useMemo(
    () => new Map(machines.map((machine) => [machine.id, machine])),
    [machines],
  )

  const availableMachines = useMemo(
    () => machines.filter((machine) => !lineCode || machine.line_code === lineCode),
    [lineCode, machines],
  )

  const filteredAlarms = useMemo(
    () =>
      alarms.filter((alarm) => {
        const machine = machineMap.get(alarm.machine_id)
        const matchesMachine = !appliedQuery.machine_id || alarm.machine_id === appliedQuery.machine_id
        const matchesLine = !appliedQuery.line_code || machine?.line_code === appliedQuery.line_code
        const matchesLevel = !alarmLevel || alarm.level === alarmLevel
        return matchesMachine && matchesLine && matchesLevel
      }),
    [alarmLevel, alarms, appliedQuery.line_code, appliedQuery.machine_id, machineMap],
  )

  const applyFilters = () => {
    const nextQuery: ProductionQuery = {
      machine_id: machineId,
      line_code: lineCode,
      product_code: productCode.trim() || undefined,
      start_date: startDate?.format('YYYY-MM-DD'),
      end_date: endDate?.format('YYYY-MM-DD'),
    }
    setAppliedQuery(nextQuery)

    const nextParams = new URLSearchParams()
    Object.entries(nextQuery).forEach(([key, value]) => {
      if (value !== undefined) nextParams.set(key, String(value))
    })
    setSearchParams(nextParams, { replace: true })

    if (machineId) selection.selectMachine(machineId, lineCode)
    else selection.selectLine(lineCode)
  }

  const resetFilters = () => {
    setLineCode(undefined)
    setMachineId(undefined)
    setProductCode('')
    setStartDate(null)
    setEndDate(null)
    setAppliedQuery({})
    setSearchParams({}, { replace: true })
    selection.selectLine(undefined)
  }

  const trendOption = useMemo<EChartsOption>(() => {
    const daily = new Map<string, { planned: number; actual: number; defects: number }>()
    records.forEach((record) => {
      const current = daily.get(record.production_date) || { planned: 0, actual: 0, defects: 0 }
      current.planned += record.planned_qty
      current.actual += record.actual_qty
      current.defects += record.defect_qty
      daily.set(record.production_date, current)
    })
    const dates = [...daily.keys()].sort()

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['计划产量', '实际产量', '不良品数'], top: 0 },
      grid: { left: 54, right: 24, top: 44, bottom: 42 },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: dates.length > 15 ? 35 : 0 } },
      yAxis: { type: 'value', name: '数量' },
      dataZoom: dates.length > 20 ? [{ type: 'inside' }, { type: 'slider', height: 18 }] : undefined,
      series: [
        { name: '计划产量', type: 'line', smooth: true, data: dates.map((date) => daily.get(date)?.planned), itemStyle: { color: '#8c8c8c' } },
        { name: '实际产量', type: 'line', smooth: true, data: dates.map((date) => daily.get(date)?.actual), itemStyle: { color: '#1677ff' } },
        { name: '不良品数', type: 'bar', data: dates.map((date) => daily.get(date)?.defects), itemStyle: { color: '#ff7875' } },
      ],
    }
  }, [records])

  const openCreateOrder = (targetMachineId?: number) => {
    const id = targetMachineId || appliedQuery.machine_id
    const params = new URLSearchParams({ create: '1' })
    if (id) params.set('machine_id', String(id))
    if (appliedQuery.line_code) params.set('line_code', appliedQuery.line_code)
    navigate(`/work-orders?${params.toString()}`)
  }

  const resolveAlarm = async (alarmId: number) => {
    setResolvingId(alarmId)
    try {
      await mesApi.resolveAlarm(alarmId)
      message.success('报警已标记为恢复')
      await load()
    } catch (requestError) {
      message.error(getErrorMessage(requestError))
    } finally {
      setResolvingId(undefined)
    }
  }

  const productionColumns: ColumnsType<ProductionRecord> = [
    { title: '日期', dataIndex: 'production_date', key: 'production_date', sorter: (a, b) => a.production_date.localeCompare(b.production_date) },
    { title: '产线', dataIndex: 'line_code', key: 'line_code' },
    { title: '设备', dataIndex: 'machine_id', key: 'machine_id', render: (id: number) => machineMap.get(id)?.code || `#${id}` },
    { title: '产品', dataIndex: 'product_code', key: 'product_code' },
    { title: '计划', dataIndex: 'planned_qty', key: 'planned_qty', render: formatNumber },
    { title: '实际', dataIndex: 'actual_qty', key: 'actual_qty', render: formatNumber },
    {
      title: '完成率',
      key: 'completion_rate',
      render: (_, record) => {
        const rate = record.planned_qty ? (record.actual_qty / record.planned_qty) * 100 : 0
        return <Tag color={rate >= 95 ? 'success' : rate >= 85 ? 'warning' : 'error'}>{rate.toFixed(1)}%</Tag>
      },
    },
    {
      title: '不良数',
      dataIndex: 'defect_qty',
      key: 'defect_qty',
      render: (value: number) => <span className={value > 0 ? 'danger-text' : ''}>{formatNumber(value)}</span>,
    },
  ]

  const alarmColumns: ColumnsType<Alarm> = [
    { title: '报警编码', dataIndex: 'alarm_code', key: 'alarm_code', width: 120 },
    { title: '设备', dataIndex: 'machine_id', key: 'machine_id', width: 120, render: (id: number) => machineMap.get(id)?.code || `#${id}` },
    { title: '内容', dataIndex: 'alarm_message', key: 'alarm_message' },
    { title: '等级', dataIndex: 'level', key: 'level', width: 90, render: (level: string) => <StatusTag value={level} map={alarmLevelMap} /> },
    { title: '发生时间', dataIndex: 'started_at', key: 'started_at', width: 180, render: formatDateTime },
    { title: '状态', key: 'status', width: 100, render: (_, alarm) => alarm.ended_at ? <Tag color="success">已恢复</Tag> : <Tag color="error">未恢复</Tag> },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 210,
      render: (_, alarm) => (
        <Space size={0}>
          {!alarm.ended_at ? (
            <Popconfirm title="确认该报警已经恢复？" onConfirm={() => void resolveAlarm(alarm.id)}>
              <Button type="link" loading={resolvingId === alarm.id} icon={<CheckOutlined />}>恢复</Button>
            </Popconfirm>
          ) : null}
          <Button type="link" icon={<PlusOutlined />} onClick={() => openCreateOrder(alarm.machine_id)}>创建工单</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageTitle
        title="设备报警与生产"
        description="基于所选产线/设备查看报警，并用 ECharts 展示真实生产记录趋势。"
        extra={<Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>刷新</Button>}
      />

      {error ? <RequestError message={error} onRetry={() => void load()} /> : null}

      <Card size="small" className="section-card" title="数据筛选">
        <Space wrap className="filter-bar no-margin">
          <Select
            allowClear
            placeholder="全部产线"
            value={lineCode}
            onChange={(value) => {
              setLineCode(value)
              if (machineId && machines.find((item) => item.id === machineId)?.line_code !== value) setMachineId(undefined)
            }}
            options={lines.map((value) => ({ label: value, value }))}
            style={{ width: 150 }}
          />
          <Select
            showSearch
            allowClear
            optionFilterProp="label"
            placeholder="全部设备"
            value={machineId}
            onChange={(value) => {
              setMachineId(value)
              const machine = machines.find((item) => item.id === value)
              if (machine?.line_code) setLineCode(machine.line_code)
            }}
            options={availableMachines.map((machine) => ({ label: `${machine.code} · ${machine.name}`, value: machine.id }))}
            style={{ width: 230 }}
          />
          <Input allowClear placeholder="产品编码" value={productCode} onChange={(event) => setProductCode(event.target.value)} style={{ width: 150 }} />
          <DatePicker placeholder="开始日期" value={startDate} onChange={setStartDate} disabledDate={(date) => Boolean(endDate && date.isAfter(endDate, 'day'))} />
          <DatePicker placeholder="结束日期" value={endDate} onChange={setEndDate} disabledDate={(date) => Boolean(startDate && date.isBefore(startDate, 'day'))} />
          <Button type="primary" icon={<SearchOutlined />} onClick={applyFilters}>查询</Button>
          <Button onClick={resetFilters}>重置</Button>
        </Space>
      </Card>

      <Row gutter={[12, 12]} className="summary-row">
        <Col xs={12} lg={6}><Card size="small"><Statistic title="生产记录" value={summary.record_count} suffix="条" /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="实际 / 计划产量" value={summary.actual_qty} suffix={`/ ${formatNumber(summary.planned_qty)}`} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="生产完成率" value={summary.completion_rate} precision={1} suffix="%" valueStyle={{ color: summary.completion_rate >= 95 ? '#389e0d' : '#d46b08' }} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="不良率" value={summary.defect_rate} precision={2} suffix="%" valueStyle={{ color: summary.defect_rate > 3 ? '#cf1322' : undefined }} /></Card></Col>
      </Row>

      <Card id="production-section" title="生产趋势" size="small" className="section-card" loading={loading}>
        {records.length ? (
          <ReactECharts option={trendOption} notMerge style={{ height: 340 }} />
        ) : (
          <div className="empty-chart">当前筛选条件下暂无生产趋势数据</div>
        )}
      </Card>

      <Card title="生产记录" size="small" className="section-card">
        <Table<ProductionRecord>
          rowKey="id"
          loading={loading}
          columns={productionColumns}
          dataSource={records}
          scroll={{ x: 900 }}
          pagination={{ defaultPageSize: 8, showSizeChanger: true, pageSizeOptions: [8, 16, 30], showTotal: (total) => `共 ${total} 条生产记录` }}
        />
      </Card>

      <Card
        id="alarm-section"
        title="设备报警"
        size="small"
        className="section-card"
        extra={
          <Space>
            <Select
              value={activeOnly ? 'active' : 'all'}
              onChange={(value) => setActiveOnly(value === 'active')}
              options={[{ label: '全部状态', value: 'all' }, { label: '仅未恢复', value: 'active' }]}
              style={{ width: 125 }}
            />
            <Select
              allowClear
              placeholder="全部等级"
              value={alarmLevel}
              onChange={setAlarmLevel}
              options={Object.entries(alarmLevelMap).map(([value, item]) => ({ value, label: item.text }))}
              style={{ width: 120 }}
            />
          </Space>
        }
      >
        <Table<Alarm>
          rowKey="id"
          loading={loading}
          columns={alarmColumns}
          dataSource={filteredAlarms}
          scroll={{ x: 1050 }}
          pagination={{ defaultPageSize: 5, showSizeChanger: true, pageSizeOptions: [5, 10, 20], showTotal: (total) => `共 ${total} 条报警` }}
        />
      </Card>
    </div>
  )
}
