export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: string
  status?: 'streaming' | 'completed' | 'cancelled' | 'error'
}

export interface Conversation {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messages: ChatMessage[]
}

export interface AgentHistoryMessage {
  role: ChatRole
  content: string
}

export interface AgentChatRequest {
  message: string
  history: AgentHistoryMessage[]
}

export interface AgentChatResponse {
  answer: string
}

export type AgentStreamEvent =
  | { type: 'status'; message: string }
  | { type: 'delta'; content: string }
  | { type: 'reset' }
  | { type: 'done'; answer: string }
  | { type: 'error'; message: string }

export interface AgentStreamHandlers {
  onStatus: (message: string) => void
  onDelta: (content: string) => void
  onReset: () => void
  onDone: (answer: string) => void
}
