import { DeleteOutlined, MessageOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Empty, List, Popconfirm, Typography } from 'antd'
import type { Conversation } from '../types/chat'
import { formatDateTime } from '../utils/format'

interface ConversationSidebarProps {
  conversations: Conversation[]
  activeId?: string
  disabled?: boolean
  onCreate: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

export function ConversationSidebar({
  conversations,
  activeId,
  disabled = false,
  onCreate,
  onSelect,
  onDelete,
}: ConversationSidebarProps) {
  return (
    <aside className="conversation-sidebar">
      <Button block type="primary" icon={<PlusOutlined />} onClick={onCreate} disabled={disabled}>
        新建对话
      </Button>

      <div className="conversation-sidebar-title">对话历史</div>
      {conversations.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无历史对话" />
      ) : (
        <List
          className="conversation-list"
          dataSource={conversations}
          renderItem={(conversation) => (
            <List.Item
              className={`conversation-list-item${conversation.id === activeId ? ' active' : ''}`}
              onClick={() => {
                if (!disabled) onSelect(conversation.id)
              }}
              actions={[
                <Popconfirm
                  key="delete"
                  title="删除该对话？"
                  description="删除后无法恢复。"
                  okText="删除"
                  cancelText="取消"
                  onConfirm={() => onDelete(conversation.id)}
                >
                  <Button
                    type="text"
                    size="small"
                    danger
                    disabled={disabled}
                    aria-label={`删除对话：${conversation.title}`}
                    icon={<DeleteOutlined />}
                    onClick={(event) => event.stopPropagation()}
                  />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<MessageOutlined />}
                title={<Typography.Text ellipsis>{conversation.title}</Typography.Text>}
                description={
                  `${conversation.messages.length} 条消息 · ${formatDateTime(conversation.updatedAt)}`
                }
              />
            </List.Item>
          )}
        />
      )}
    </aside>
  )
}
