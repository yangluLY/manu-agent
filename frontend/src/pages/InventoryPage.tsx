import { PlusOutlined, ReloadOutlined, WarningOutlined } from '@ant-design/icons'
import { Button, Card, Col, Input, Progress, Row, Select, Space, Statistic, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageTitle } from '../components/PageTitle'
import { RequestError } from '../components/RequestError'
import { useSelection } from '../context/SelectionContext'
import { getErrorMessage, mesApi } from '../services/api'
import type { Material } from '../types/api'
import { formatNumber } from '../utils/format'

type StockFilter = 'all' | 'low' | 'safe'

export function InventoryPage() {
  const navigate = useNavigate()
  const { machineId, lineCode } = useSelection()
  const [materials, setMaterials] = useState<Material[]>([])
  const [lowStockIds, setLowStockIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [keyword, setKeyword] = useState('')
  const [stockFilter, setStockFilter] = useState<StockFilter>('all')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [all, lowStock] = await Promise.all([
        mesApi.getMaterials(),
        mesApi.getLowStockMaterials(),
      ])
      setMaterials(all)
      setLowStockIds(new Set(lowStock.map((item) => item.id)))
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const filteredMaterials = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase()
    return materials.filter((material) => {
      const matchesKeyword =
        !lowerKeyword ||
        material.code.toLowerCase().includes(lowerKeyword) ||
        material.name.toLowerCase().includes(lowerKeyword)
      const isLow = lowStockIds.has(material.id)
      const matchesStock = stockFilter === 'all' || (stockFilter === 'low' ? isLow : !isLow)
      return matchesKeyword && matchesStock
    })
  }, [keyword, lowStockIds, materials, stockFilter])

  const columns: ColumnsType<Material> = [
    {
      title: '物料',
      key: 'material',
      render: (_, material) => (
        <div>
          <strong>{material.code}</strong>
          <div className="secondary-text">{material.name}</div>
        </div>
      ),
    },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 100 },
    {
      title: '当前库存',
      dataIndex: 'stock_qty',
      key: 'stock_qty',
      render: (value: number | string, material) => (
        <strong className={lowStockIds.has(material.id) ? 'danger-text' : ''}>
          {formatNumber(value)} {material.unit}
        </strong>
      ),
      sorter: (a, b) => Number(a.stock_qty) - Number(b.stock_qty),
    },
    {
      title: '安全库存',
      dataIndex: 'safe_stock',
      key: 'safe_stock',
      render: (value: number | string, material) => `${formatNumber(value)} ${material.unit}`,
    },
    {
      title: '库存水平',
      key: 'ratio',
      width: 220,
      render: (_, material) => {
        const safeStock = Number(material.safe_stock)
        const ratio = safeStock > 0 ? Math.round((Number(material.stock_qty) / safeStock) * 100) : 100
        const percent = Math.min(ratio, 100)
        return (
          <Progress
            percent={percent}
            format={() => `${ratio}%`}
            status={ratio < 100 ? 'exception' : 'success'}
            size="small"
          />
        )
      },
    },
    {
      title: '状态',
      key: 'status',
      render: (_, material) =>
        lowStockIds.has(material.id) ? (
          <Tag color="error" icon={<WarningOutlined />}>低库存</Tag>
        ) : (
          <Tag color="success">库存正常</Tag>
        ),
    },
  ]

  const openCreateOrder = () => {
    const query = new URLSearchParams({ create: '1' })
    if (machineId) query.set('machine_id', String(machineId))
    if (lineCode) query.set('line_code', lineCode)
    navigate(`/work-orders?${query.toString()}`)
  }

  return (
    <div>
      <PageTitle
        title="库存管理"
        description="识别安全库存风险；低库存数据同时调用 FastAPI 的专用查询接口进行校验。"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateOrder}>
              创建维修工单
            </Button>
          </Space>
        }
      />

      {error ? <RequestError message={error} onRetry={() => void load()} /> : null}

      <Row gutter={[12, 12]} className="summary-row">
        <Col xs={12} lg={6}><Card size="small"><Statistic title="物料种类" value={materials.length} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="低库存物料" value={lowStockIds.size} valueStyle={{ color: lowStockIds.size ? '#cf1322' : '#389e0d' }} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="库存正常" value={materials.length - lowStockIds.size} /></Card></Col>
        <Col xs={12} lg={6}><Card size="small"><Statistic title="库存风险率" value={materials.length ? (lowStockIds.size / materials.length) * 100 : 0} precision={1} suffix="%" /></Card></Col>
      </Row>

      <Card title="物料库存" size="small" className="section-card">
        <Space wrap className="filter-bar">
          <Input.Search
            allowClear
            placeholder="搜索物料编码或名称"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            style={{ width: 260 }}
          />
          <Select<StockFilter>
            value={stockFilter}
            onChange={setStockFilter}
            options={[
              { label: '全部库存状态', value: 'all' },
              { label: '仅低库存', value: 'low' },
              { label: '仅库存正常', value: 'safe' },
            ]}
            style={{ width: 160 }}
          />
        </Space>
        <Table<Material>
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={filteredMaterials}
          scroll={{ x: 900 }}
          pagination={{
            defaultPageSize: 8,
            showSizeChanger: true,
            pageSizeOptions: [8, 16, 30],
            showTotal: (total) => `共 ${total} 种物料`,
          }}
        />
      </Card>
    </div>
  )
}
