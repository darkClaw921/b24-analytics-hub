import { useState, KeyboardEvent } from 'react'

interface MessageInputProps {
  onSend: (message: string) => Promise<any>
  loading: boolean
}

export default function MessageInput({ onSend, loading }: MessageInputProps) {
  const [message, setMessage] = useState('')

  const handleSend = async () => {
    if (!message.trim() || loading) return

    try {
      await onSend(message)
      setMessage('')
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="message-input-container">
      <textarea
        className="message-input"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Введите сообщение... (Enter для отправки, Shift+Enter для новой строки)"
        disabled={loading}
        rows={3}
      />
      <button
        className="btn btn-primary btn-send"
        onClick={handleSend}
        disabled={!message.trim() || loading}
      >
        {loading ? 'Отправка...' : 'Отправить'}
      </button>
    </div>
  )
}

