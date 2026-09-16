import {
  AlertOutlined,
  ApartmentOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import { Badge, Button, Layout, Menu } from 'antd'
import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { mesApi } from '../services/api'
import { WorkflowBar } from '../components/WorkflowBar'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/equipment', icon: <ApartmentOutlined />, label: '产线与设备' },
  { key: '/production', icon: <AlertOutlined />, label: '报警与生产' },
  { key: '/inventory', icon: <DatabaseOutlined />, label: '库存管理' },
  { key: '/work-orders', icon: <ToolOutlined />, label: '维修工单' },
]

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    let active = true
    mesApi
      .health()
      .then(() => active && setApiOnline(true))
      .catch(() => active && setApiOnline(false))
    return () => {
      active = false
    }
  }, [location.pathname])

  return (
    <Layout className="app-shell">
      <Sider collapsible collapsed={collapsed} trigger={null} theme="dark">
        <div className="brand">{collapsed ? 'MA' : 'ManuAgent'}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <div className="header-left">
            <Button
              type="text"
              aria-label={collapsed ? '展开导航' : '收起导航'}
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed((value) => !value)}
            />
            <span className="factory-name">当前工厂：杭州工厂</span>
          </div>
          <Badge
            status={apiOnline === null ? 'processing' : apiOnline ? 'success' : 'error'}
            text={apiOnline === null ? '检测 FastAPI' : apiOnline ? 'FastAPI 已连接' : 'FastAPI 未连接'}
          />
        </Header>
        <WorkflowBar />
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
