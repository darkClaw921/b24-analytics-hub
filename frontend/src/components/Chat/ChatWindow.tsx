import { useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useChat } from '../../hooks/useChat'
import { wsService } from '../../services/websocket'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import TokenCounter from './TokenCounter'
import ToolButtons from './ToolButtons'

export default function ChatWindow() {
  const { chatId } = useParams<{ chatId: string }>()
  const navigate = useNavigate()
  const { messages, chat, loading, error, sendMessage, refreshMessages } = useChat(
    chatId ? parseInt(chatId) : null
  )

  useEffect(() => {
    if (!chatId) return

    // Connect to WebSocket
    wsService.connect(parseInt(chatId), (data) => {
      // Handle WebSocket messages (e.g., real-time updates)
      console.log('WebSocket message:', data)
      refreshMessages()
    })

    return () => {
      wsService.disconnect()
    }
  }, [chatId])

  if (!chatId) {
    return <div>Chat not found</div>
  }

  return (
    <div className="chat-window">
      <header className="chat-header">
        <button className="btn-back" onClick={() => navigate('/')}>
          ← Назад
        </button>
        <h2>{chat?.title || 'Чат'}</h2>
        <TokenCounter totalTokens={chat?.total_tokens || 0} />
      </header>

      <div className="chat-content">
        <MessageList messages={messages} loading={loading} />
        
        <ToolButtons chatId={parseInt(chatId)} onToolResult={refreshMessages} />
        
        <MessageInput onSend={sendMessage} loading={loading} />
        
        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  )
}

