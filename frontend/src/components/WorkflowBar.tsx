import { Steps } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'
import { useSelection } from '../context/SelectionContext'

const stages = [
  { title: '查看产线', path: '/equipment?view=lines' },
  { title: '查看设备', path: '/equipment?view=machines' },
  { title: '设备报警', path: '/production?view=alarms' },
  { title: '生产数据', path: '/production?view=production' },
  { title: '查看库存', path: '/inventory' },
  { title: '创建工单', path: '/work-orders?create=1' },
  { title: '更新状态', path: '/work-orders' },
]

export function WorkflowBar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { machineId, lineCode } = useSelection()

  let current = 0
  const view = new URLSearchParams(location.search).get('view')
  if (location.pathname === '/equipment') {
    current = view === 'lines' ? 0 : view === 'machines' || machineId ? 1 : 0
  }
  if (location.pathname === '/production') current = view === 'alarms' ? 2 : 3
  if (location.pathname === '/inventory') current = 4
  if (location.pathname === '/work-orders') current = location.search.includes('create=1') ? 5 : 6

  const goTo = (path: string) => {
    const query = new URLSearchParams()
    if (machineId) query.set('machine_id', String(machineId))
    if (lineCode) query.set('line_code', lineCode)

    if (path.includes('?')) {
      const [pathname, existing] = path.split('?')
      const existingParams = new URLSearchParams(existing)
      existingParams.forEach((value, key) => query.set(key, value))
      navigate(`${pathname}?${query.toString()}`)
      return
    }
    navigate(query.size ? `${path}?${query.toString()}` : path)
  }

  return (
    <div className="workflow-bar">
      <div className="workflow-label">业务路径</div>
      <Steps
        size="small"
        current={current}
        responsive={false}
        items={stages.map((stage) => ({
          title: stage.title,
          onClick: () => goTo(stage.path),
          className: 'workflow-step',
        }))}
      />
    </div>
  )
}
