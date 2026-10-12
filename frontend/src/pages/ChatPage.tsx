import { EditOutlined, RedditSquareFilled, RobotOutlined, SendOutlined, StopOutlined, UserOutlined } from '@ant-design/icons'
import { Alert, Avatar, Button, Empty, Input, Spin, Tag, Typography } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ConversationSidebar } from '../components/ConversationSidebar'
import { agentApi, getErrorMessage } from '../services/api'
import {
  createConversation,
  createMessage,
  deleteConversation,
  getConversation,
  listConversations,
  saveConversation,
  titleFromMessage,
} from '../services/conversationStore'
import type { Conversation } from '../types/chat'
import { formatDateTime } from '../utils/format'

const { TextArea } = Input

const suggestions = [
  '查询当前有哪些设备报警',
  '分析设备 MC-003 最近的生产指标',
  '查询低库存物料并给出处理建议',
]

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>(() => listConversations())
  const [conversation, setConversation] = useState<Conversation>()
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [streamingMessageId, setStreamingMessageId] = useState<string>()
  const [streamStatus, setStreamStatus] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | undefined>(undefined)

  useEffect(() => {
    const stored = listConversations()
    setConversations(stored)

    if (!conversationId) {
      const target = stored[0] ?? createConversation()
      navigate(`/chat/${target.id}`, { replace: true })
      return
    }

    const selected = getConversation(conversationId)
    if (selected) {
      setConversation(selected)
      setError('')
      return
    }

    const created = createConversation()
    navigate(`/chat/${created.id}`, { replace: true })
  }, [conversationId, navigate])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: sending ? 'auto' : 'smooth' })
  }, [conversation?.messages, sending])

  useEffect(
    () => () => {
      abortControllerRef.current?.abort()
    },
    [],
  )

  const refreshConversations = () => setConversations(listConversations())

  const startConversation = () => {
    const created = createConversation()
    refreshConversations()
    navigate(`/chat/${created.id}`)
  }

  const removeConversation = (id: string) => {
    deleteConversation(id)
    const remaining = listConversations()
    setConversations(remaining)
    if (conversationId === id) {
      if (remaining[0]) navigate(`/chat/${remaining[0].id}`)
      else navigate('/chat')
    }
  }

  const sendMessage = async () => {
    const content = draft.trim()
    if (!content || !conversation || sending) return

    const currentConversation = conversation
    const previousMessages = currentConversation.messages
    const historyMessages = previousMessages.filter(
      (message) => !message.status || message.status === 'completed',
    )
    const userMessage = createMessage('user', content)
    const assistantMessage = {
      ...createMessage('assistant', ''),
      status: 'streaming' as const,
    }
    const pendingConversation = saveConversation({
      ...currentConversation,
      title:
        currentConversation.messages.length === 0
          ? titleFromMessage(content)
          : currentConversation.title,
      messages: [...previousMessages, userMessage],
    })

    setConversation({
      ...pendingConversation,
      messages: [...pendingConversation.messages, assistantMessage],
    })
    refreshConversations()
    setDraft('')
    setError('')
    setSending(true)
    setStreamingMessageId(assistantMessage.id)
    setStreamStatus('ManuAgent 正在分析问题…')

    const abortController = new AbortController()
    abortControllerRef.current = abortController
    let streamedContent = ''
    let finalAnswer = ''

    const updateStreamingMessage = (content: string) => {
      setConversation((current) => {
        if (!current || current.id !== currentConversation.id) return current
        return {
          ...current,
          messages: current.messages.map((message) =>
            message.id === assistantMessage.id ? { ...message, content } : message,
          ),
        }
      })
    }

    try {
      await agentApi.streamChat(
        {
          message: content,
          history: historyMessages.slice(-50).map((message) => ({
            role: message.role,
            content: message.content.slice(0, 8000),
          })),
        },
        {
          onStatus: setStreamStatus,
          onDelta: (delta) => {
            streamedContent += delta
            setStreamStatus('')
            updateStreamingMessage(streamedContent)
          },
          onReset: () => {
            streamedContent = ''
            setStreamStatus('ManuAgent 正在调用业务工具…')
            updateStreamingMessage('')
          },
          onDone: (answer) => {
            finalAnswer = answer
            streamedContent = answer
            updateStreamingMessage(answer)
          },
        },
        abortController.signal,
      )

      const answer = finalAnswer || streamedContent
      if (!answer.trim()) throw new Error('Agent 没有返回回答内容')

      const latest = getConversation(currentConversation.id) ?? pendingConversation
      const completed = saveConversation({
        ...latest,
        messages: [
          ...latest.messages,
          {
            ...assistantMessage,
            content: answer,
            status: 'completed',
          },
        ],
      })
      if (conversationId === currentConversation.id) setConversation(completed)
      refreshConversations()
    } catch (requestError) {
      const latest = getConversation(currentConversation.id) ?? pendingConversation
      const aborted = abortController.signal.aborted
      const hasPartialAnswer = Boolean(streamedContent.trim())
      const interruptedStatus = aborted ? ('cancelled' as const) : ('error' as const)
      const interruptedMessages = latest.messages.map((message) =>
        message.id === userMessage.id
          ? { ...message, status: interruptedStatus }
          : message,
      )
      const restored = saveConversation(
        hasPartialAnswer
          ? {
              ...latest,
              messages: [
                ...interruptedMessages,
                {
                  ...assistantMessage,
                  content: streamedContent,
                  status: interruptedStatus,
                },
              ],
            }
          : {
              ...latest,
              messages: aborted
                ? interruptedMessages
                : latest.messages.filter((message) => message.id !== userMessage.id),
            },
      )
      if (conversationId === currentConversation.id) {
        setConversation(restored)
        if (!aborted && !hasPartialAnswer) setDraft(content)
        setError(aborted ? '已停止生成' : getErrorMessage(requestError))
      }
      refreshConversations()
    } finally {
      abortControllerRef.current = undefined
      setSending(false)
      setStreamingMessageId(undefined)
      setStreamStatus('')
    }
  }

  return (
    <div className="chat-page">
      <ConversationSidebar
        conversations={conversations}
        activeId={conversationId}
        disabled={sending}
        onCreate={startConversation}
        onSelect={(id) => navigate(`/chat/${id}`)}
        onDelete={removeConversation}
      />

      <section className="chat-panel">
        <header className="chat-panel-header">
          <div>
            <h1>{conversation?.title ?? 'ManuAgent 对话'}</h1>
            <span>DeepSeek · MES 实时数据 · 企业知识库 RAG</span>
          </div>
          <span className="chat-message-count">{conversation?.messages.length ?? 0} 条消息</span>
        </header>

        <div className="chat-messages" aria-live="polite">
          {conversation?.messages.length ? (
            conversation.messages.map((message) => {
              const isStreaming = sending && message.id === streamingMessageId
              return (
                <article key={message.id} className={`chat-message ${message.role}`}>
                <Avatar
                  className="chat-avatar"
                  icon={message.role === 'user' ? <EditOutlined /> : <RedditSquareFilled />}
                />
                <div className="chat-bubble">
                  <div className="chat-message-meta">
                    <strong>{message.role === 'user' ? '我' : 'ManuAgent'}</strong>
                    <span>{formatDateTime(message.createdAt)}</span>
                    {message.status === 'cancelled' ? <Tag>已停止</Tag> : null}
                    {message.status === 'error' ? <Tag color="error">输出中断</Tag> : null}
                  </div>
                  {isStreaming && !message.content ? (
                    <div className="chat-thinking">
                      <Spin size="small" />
                      <span>{streamStatus || 'ManuAgent 正在生成回答…'}</span>
                    </div>
                  ) : (
                    <Typography.Paragraph className="chat-message-content">
                      {message.content}
                      {isStreaming ? <span className="streaming-cursor" /> : null}
                    </Typography.Paragraph>
                  )}
                </div>
              </article>
              )
            })
          ) : (
            <div className="chat-empty">
              <Empty description="开始一次 MES 智能对话" />
              <div className="chat-suggestions">
                {suggestions.map((suggestion) => (
                  <Button key={suggestion} onClick={() => setDraft(suggestion)}>
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <footer className="chat-composer">
          {error ? (
            <Alert
              showIcon
              closable
              type="error"
              message={error === '已停止生成' ? '已停止生成' : '发送失败'}
              description={
                error === '已停止生成'
                  ? '已保留当前获得的内容。'
                  : `${error}。可检查后端状态后重试。`
              }
              onClose={() => setError('')}
            />
          ) : null}
          <div className="chat-input-row">
            <TextArea
              value={draft}
              maxLength={2000}
              autoSize={{ minRows: 2, maxRows: 6 }}
              placeholder="输入设备、报警、生产、库存、工单或企业知识库问题；Enter 发送，Shift+Enter 换行"
              disabled={!conversation || sending}
              onChange={(event) => setDraft(event.target.value)}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault()
                  void sendMessage()
                }
              }}
            />
            {sending ? (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={() => abortControllerRef.current?.abort()}
              >
                停止
              </Button>
            ) : (
              <Button
                type="primary"
                icon={<SendOutlined />}
                disabled={!draft.trim() || !conversation}
                onClick={() => void sendMessage()}
              >
                发送
              </Button>
            )}
          </div>
          <span className="chat-composer-tip">会话历史保存在当前浏览器，并随每次请求发送给 ManuAgent。</span>
        </footer>
      </section>
    </div>
  )
}
