import type { ChatMessage, Conversation } from '../types/chat'

const STORAGE_KEY = 'manu-agent.conversations.v1'

function createId(prefix: string): string {
  const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`
  return `${prefix}-${id}`
}

function isMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== 'object') return false
  const message = value as Partial<ChatMessage>
  return (
    typeof message.id === 'string' &&
    (message.role === 'user' || message.role === 'assistant') &&
    typeof message.content === 'string' &&
    typeof message.createdAt === 'string' &&
    (message.status === undefined ||
      ['streaming', 'completed', 'cancelled', 'error'].includes(message.status))
  )
}

function isConversation(value: unknown): value is Conversation {
  if (!value || typeof value !== 'object') return false
  const conversation = value as Partial<Conversation>
  return (
    typeof conversation.id === 'string' &&
    typeof conversation.title === 'string' &&
    typeof conversation.createdAt === 'string' &&
    typeof conversation.updatedAt === 'string' &&
    Array.isArray(conversation.messages) &&
    conversation.messages.every(isMessage)
  )
}

function write(conversations: Conversation[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
}

export function listConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter(isConversation)
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
  } catch {
    return []
  }
}

export function getConversation(id: string): Conversation | undefined {
  return listConversations().find((conversation) => conversation.id === id)
}

export function createConversation(): Conversation {
  const now = new Date().toISOString()
  const conversation: Conversation = {
    id: createId('conversation'),
    title: '新对话',
    createdAt: now,
    updatedAt: now,
    messages: [],
  }
  write([conversation, ...listConversations()])
  return conversation
}

export function saveConversation(conversation: Conversation): Conversation {
  const conversations = listConversations().filter((item) => item.id !== conversation.id)
  const saved = { ...conversation, updatedAt: new Date().toISOString() }
  write([saved, ...conversations])
  return saved
}

export function deleteConversation(id: string): void {
  write(listConversations().filter((conversation) => conversation.id !== id))
}

export function createMessage(role: ChatMessage['role'], content: string): ChatMessage {
  return {
    id: createId('message'),
    role,
    content,
    createdAt: new Date().toISOString(),
    status: 'completed',
  }
}

export function titleFromMessage(message: string): string {
  const normalized = message.replace(/\s+/g, ' ').trim()
  return normalized.length > 24 ? `${normalized.slice(0, 24)}…` : normalized || '新对话'
}
