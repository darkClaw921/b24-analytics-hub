import { Message } from '../../types'
import { useEffect, useRef, useState } from 'react'

interface MessageListProps {
  messages: Message[]
  loading: boolean
}

export default function MessageList({ messages, loading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const [showScrollUp, setShowScrollUp] = useState(false)
  const [showScrollDown, setShowScrollDown] = useState(false)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const container = messagesContainerRef.current
    if (!container) return

    const checkScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container
      const isAtTop = scrollTop < 100
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 100
      
      setShowScrollUp(!isAtTop && scrollHeight > clientHeight)
      setShowScrollDown(!isAtBottom && scrollHeight > clientHeight)
    }

    checkScroll()
    container.addEventListener('scroll', checkScroll)
    
    return () => {
      container.removeEventListener('scroll', checkScroll)
    }
  }, [messages, loading])

  const scrollToTop = () => {
    messagesContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="message-list-wrapper">
      <div className="message-list" ref={messagesContainerRef}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message message-${message.role}`}
          >
            <div className="message-role">
              {message.role === 'user' && '👤 Вы'}
              {message.role === 'assistant' && '🤖 Ассистент'}
              {message.role === 'tool' && `🔧 ${message.tool_name}`}
            </div>
            <div className="message-content">
              {message.content}
            </div>
            {message.tokens_used > 0 && (
              <div className="message-meta">
                {message.tokens_used} токенов
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message message-assistant">
            <div className="message-role">🤖 Ассистент</div>
            <div className="message-content typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {showScrollUp && (
        <button 
          className="scroll-button scroll-button-up"
          onClick={scrollToTop}
          title="Прокрутить вверх"
        >
          ↑
        </button>
      )}
      
      {showScrollDown && (
        <button 
          className="scroll-button scroll-button-down"
          onClick={scrollToBottom}
          title="Прокрутить вниз"
        >
          ↓
        </button>
      )}
    </div>
  )
}

