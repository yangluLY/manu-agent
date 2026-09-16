import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  App as AntdApp,
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { PageTitle } from '../components/PageTitle'
import { RequestError } from '../components/RequestError'
import { StatusTag } from '../components/StatusTag'
import { useSelection } from '../context/SelectionContext'
import { getErrorMessage, mesApi } from '../services/api'
import type {
  CreateWorkOrderPayload,
  Machine,
  WorkOrder,
  WorkOrderPriority,
  WorkOrderStatus,
  WorkOrderType,
} from '../types/api'
import {
  formatDateTime,
  workOrderPriorityMap,
  workOrderStatusMap,
  workOrderTypeMap,
} from '../utils/format'

export function WorkOrdersPage() {
  const { message } = AntdApp.useApp()
  const [form] = Form.useForm<CreateWorkOrderPayload>()
  const [searchParams, setSearchParams] = useSearchParams()
  const selection = useSelection()
  const initialMachineId = Number(searchParams.get('machine_id')) || selection.machineId

  const [orders, setOrders] = useState<WorkOrder[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [updatingId, setUpdatingId] = useState<number>()
  const [modalOpen, setModalOpen] = useState(searchParams.get('create') === '1')

  const [keyword, setKeyword] = useState('')
  const [machineFilter, setMachineFilter] = useState<number | undefined>(initialMachineId)
  const [statusFilter, setStatusFilter] = useState<WorkOrderStatus>()
  const [priorityFilter, setPriorityFilter] = useState<WorkOrderPriority>()
  const [typeFilter, setTypeFilter] = useState<WorkOrderType>()

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [orderData, machineData] = await Promise.all([
        mesApi.getWorkOrders(),
        mesApi.getMachines(),
      ])
      setOrders(orderData)
      setMachines(machineData)
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
    if (searchParams.get('create') === '1') {
      setModalOpen(true)
      if (initialMachineId) form.setFieldValue('machine_id', initialMachineId)
    }
  }, [form, initialMachineId, searchParams])

  const machineMap = useMemo(
    () => new Map(machines.map((machine) => [machine.id, machine])),
    [machines],
  )

  const filteredOrders = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase()
    return orders.filter((order) => {
      const machine = machineMap.get(order.machine_id)
      const matchesKeyword =
        !lowerKeyword ||
        order.order_no.toLowerCase().includes(lowerKeyword) ||
        order.description.toLowerCase().includes(lowerKeyword) ||
        order.assigned_to?.toLowerCase().includes(lowerKeyword) ||
        machine?.code.toLowerCase().includes(lowerKeyword)
      return (
        matchesKeyword &&
        (!machineFilter || order.machine_id === machineFilter) &&
        (!statusFilter || order.status === statusFilter) &&
        (!priorityFilter || order.priority === priorityFilter) &&
        (!typeFilter || order.type === typeFilter)
      )
    })
  }, [keyword, machineFilter, machineMap, orders, priorityFilter, statusFilter, typeFilter])

  const openModal = () => {
    form.resetFields()
    form.setFieldsValue({
      machine_id: machineFilter || selection.machineId,
      type: 'repair',
      priority: 'medium',
    })
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    const next = new URLSearchParams(searchParams)
    next.delete('create')
    setSearchParams(next, { replace: true })
  }

  const createOrder = async (values: CreateWorkOrderPayload) => {
    setSubmitting(true)
    try {
      const created = await mesApi.createWorkOrder({
        ...values,
        assigned_to: values.assigned_to?.trim() || undefined,
      })
      setOrders((current) => [created, ...current])
      const machine = machineMap.get(values.machine_id)
      selection.selectMachine(values.machine_id, machine?.line_code || undefined)
      setMachineFilter(values.machine_id)
      message.success(`工单 ${created.order_no} 创建成功`)
      form.resetFields()
      closeModal()
    } catch (requestError) {
      message.error(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  const changeStatus = async (order: WorkOrder, status: WorkOrderStatus) => {
    setUpdatingId(order.id)
    try {
      const updated = await mesApi.updateWorkOrder(order.id, { status })
      setOrders((current) => current.map((item) => (item.id === order.id ? updated : item)))
      message.success(`${order.order_no} 已更新为“${workOrderStatusMap[status].text}”`)
    } catch (requestError) {
      message.error(getErrorMessage(requestError))
    } finally {
      setUpdatingId(undefined)
    }
  }

  const columns: ColumnsType<WorkOrder> = [
    {
      title: '工单编号',
      dataIndex: 'order_no',
      key: 'order_no',
      width: 180,
      render: (value: string) => <strong>{value}</strong>,
    },
    {
      title: '设备',
      dataIndex: 'machine_id',
      key: 'machine_id',
      width: 130,
      render: (id: number) => machineMap.get(id)?.code || `#${id}`,
    },
    { title: '类型', dataIndex: 'type', key: 'type', width: 90, render: (value: string) => workOrderTypeMap[value] || value },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 90,
      render: (value: string) => <StatusTag value={value} map={workOrderPriorityMap} />,
    },
    { title: '负责人', dataIndex: 'assigned_to', key: 'assigned_to', width: 100, render: (value) => value || '未分配' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (value: string) => <StatusTag value={value} map={workOrderStatusMap} />,
    },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 180, render: formatDateTime },
    {
      title: '修改状态',
      key: 'action',
      fixed: 'right',
      width: 140,
      render: (_, order) => (
        <Select<WorkOrderStatus>
          aria-label={`修改工单 ${order.order_no} 状态`}
          value={order.status}
          loading={updatingId === order.id}
          disabled={updatingId !== undefined}
          onChange={(value) => void changeStatus(order, value)}
          options={Object.entries(workOrderStatusMap).map(([value, item]) => ({
            value: value as WorkOrderStatus,
            label: item.text,
          }))}
          style={{ width: 120 }}
        />
      ),
    },
  ]

  const pendingCount = orders.filter((item) => item.status === 'pending').length
  const progressCount = orders.filter((item) => item.status === 'in_progress').length
  const urgentCount = orders.filter(
    (item) => item.priority === 'urgent' && !['completed', 'cancelled'].includes(item.status),
  ).length

  return (
    <div>
      <PageTitle
        title="维修工单"
        description="创建维修工单并直接修改工单状态，提交后立即回写 FastAPI。"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openModal}>创建工单</Button>
          </Space>
        }
      />

      {error ? <RequestError message={error} onRetry={() => void load()} /> : null}

      <Row gutter={[12, 12]} className="summary-row">
        <Col xs={12} lg={6}><Card size="small"><Statistic title="工单总数" value={orders.length} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="待处理" value={pendingCount} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="处理中" value={progressCount} valueStyle={{ color: '#1677ff' }} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="未关闭紧急工单" value={urgentCount} valueStyle={{ color: urgentCount ? '#cf1322' : undefined }} /></Card></Col>
      </Row>

      <Card title="工单列表" size="small" className="section-card">
        <Space wrap className="filter-bar">
          <Input.Search allowClear placeholder="搜索工单号、设备、描述或负责人" value={keyword} onChange={(event) => setKeyword(event.target.value)} style={{ width: 290 }} />
          <Select
            showSearch
            allowClear
            optionFilterProp="label"
            placeholder="全部设备"
            value={machineFilter}
            onChange={setMachineFilter}
            options={machines.map((machine) => ({ value: machine.id, label: `${machine.code} · ${machine.name}` }))}
            style={{ width: 220 }}
          />
          <Select allowClear placeholder="全部状态" value={statusFilter} onChange={setStatusFilter} options={Object.entries(workOrderStatusMap).map(([value, item]) => ({ value, label: item.text }))} style={{ width: 130 }} />
          <Select allowClear placeholder="全部优先级" value={priorityFilter} onChange={setPriorityFilter} options={Object.entries(workOrderPriorityMap).map(([value, item]) => ({ value, label: item.text }))} style={{ width: 130 }} />
          <Select allowClear placeholder="全部类型" value={typeFilter} onChange={setTypeFilter} options={Object.entries(workOrderTypeMap).map(([value, label]) => ({ value, label }))} style={{ width: 120 }} />
        </Space>
        <Table<WorkOrder>
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={filteredOrders}
          scroll={{ x: 1300 }}
          pagination={{ defaultPageSize: 8, showSizeChanger: true, pageSizeOptions: [8, 16, 30], showTotal: (total) => `共 ${total} 张工单` }}
        />
      </Card>

      <Modal
        title="创建维修工单"
        open={modalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        okText="提交工单"
        cancelText="取消"
        confirmLoading={submitting}
        destroyOnClose
      >
        <Form<CreateWorkOrderPayload>
          form={form}
          layout="vertical"
          initialValues={{ machine_id: initialMachineId, type: 'repair', priority: 'medium' }}
          onFinish={(values) => void createOrder(values)}
        >
          <Form.Item name="machine_id" label="设备" rules={[{ required: true, message: '请选择设备' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="选择需要维修的设备"
              options={machines.map((machine) => ({ value: machine.id, label: `${machine.code} · ${machine.name}` }))}
            />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="type" label="工单类型" rules={[{ required: true }]}>
                <Select options={Object.entries(workOrderTypeMap).map(([value, label]) => ({ value, label }))} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="priority" label="优先级" rules={[{ required: true }]}>
                <Select options={Object.entries(workOrderPriorityMap).map(([value, item]) => ({ value, label: item.text }))} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="assigned_to" label="负责人">
            <Input maxLength={100} placeholder="例如：张工（可选）" />
          </Form.Item>
          <Form.Item
            name="description"
            label="问题描述"
            rules={[
              { required: true, message: '请输入问题描述' },
              { whitespace: true, message: '问题描述不能只包含空格' },
            ]}
          >
            <Input.TextArea rows={4} maxLength={500} showCount placeholder="描述报警现象、检查要求或维修内容" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
