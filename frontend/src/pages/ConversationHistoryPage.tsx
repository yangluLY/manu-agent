import { DeleteOutlined, MessageOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Popconfirm, Space, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageTitle } from '../components/PageTitle'
import {
  createConversation,
  deleteConversation,
  listConversations,
} from '../services/conversationStore'
import type { Conversation } from '../types/chat'
import { formatDateTime } from '../utils/format'

export function ConversationHistoryPage() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>(() => listConversations())

  const startConversation = () => {
    const conversation = createConversation()
    navigate(`/chat/${conversation.id}`)
  }

  const removeConversation = (id: string) => {
    deleteConversation(id)
    setConversations(listConversations())
  }

  const columns: ColumnsType<Conversation> = [
    {
      title: '对话',
      key: 'conversation',
      render: (_, conversation) => (
        <div>
          <Typography.Text strong>{conversation.title}</Typography.Text>
          <div className="secondary-text">
            {conversation.messages.at(-1)?.content.slice(0, 80) || '尚未发送消息'}
          </div>
        </div>
      ),
    },
    {
      title: '消息数',
      key: 'messageCount',
      width: 100,
      render: (_, conversation) => conversation.messages.length,
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 190,
      render: formatDateTime,
    },
    {
      title: '最后更新',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 190,
      render: formatDateTime,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, conversation) => (
        <Space>
          <Button
            type="link"
            icon={<MessageOutlined />}
            onClick={() => navigate(`/chat/${conversation.id}`)}
          >
            打开
          </Button>
          <Popconfirm
            title="删除该对话？"
            description="删除后无法恢复。"
            okText="删除"
            cancelText="取消"
            onConfirm={() => removeConversation(conversation.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageTitle
        title="对话历史"
        description="查看保存在当前浏览器中的 ManuAgent 会话，打开后可继续多轮对话。"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={startConversation}>
            新建对话
          </Button>
        }
      />
      <Table<Conversation>
        rowKey="id"
        columns={columns}
        dataSource={conversations}
        locale={{ emptyText: '暂无对话历史' }}
        pagination={{
          defaultPageSize: 10,
          showSizeChanger: true,
          pageSizeOptions: [10, 20, 50],
          showTotal: (total) => `共 ${total} 个对话`,
        }}
      />
    </div>
  )
}
