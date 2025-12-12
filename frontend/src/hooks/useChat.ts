import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Message, Chat } from '../types'

export function useChat(chatId: number | null) {
  const [messages, setMessages] = useState<Message[]>([])
  const [chat, setChat] = useState<Chat | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (chatId) {
      loadChat()
      loadMessages()
    }
  }, [chatId])

  const loadChat = async () => {
    if (!chatId) return

    try {
      setLoading(true)
      const response = await api.get<Chat>(`/api/chats/${chatId}`)
      setChat(response.data)
    } catch (err: any) {
      setError(err.message || 'Error loading chat')
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async () => {
    if (!chatId) return

    try {
      setLoading(true)
      const response = await api.get<Message[]>(`/api/chats/${chatId}/messages`)
      setMessages(response.data)
    } catch (err: any) {
      setError(err.message || 'Error loading messages')
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async (content: string) => {
    if (!chatId) return

    try {
      setLoading(true)
      setError(null)
      
      const response = await api.post(`/api/chats/${chatId}/messages`, { content })
      
      // Reload messages after sending
      await loadMessages()
      await loadChat() // Reload to update token count
      
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Error sending message'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return {
    messages,
    chat,
    loading,
    error,
    sendMessage,
    refreshMessages: loadMessages,
  }
}

