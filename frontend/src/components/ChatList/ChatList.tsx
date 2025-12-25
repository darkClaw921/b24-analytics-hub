import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../services/api'
import { Chat } from '../../types'
import { useAuth } from '../../hooks/useAuth'

export default function ChatList() {
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewChat, setShowNewChat] = useState(false)
  const [newChatTitle, setNewChatTitle] = useState('')
  
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  useEffect(() => {
    loadChats()
  }, [])

  const loadChats = async () => {
    try {
      const response = await api.get<Chat[]>('/chats')
      setChats(response.data)
    } catch (error) {
      console.error('Error loading chats:', error)
    } finally {
      setLoading(false)
    }
  }

  const createChat = async () => {
    if (!newChatTitle.trim()) return

    try {
      const response = await api.post<Chat>('/chats', { title: newChatTitle })
      navigate(`/chat/${response.data.id}`)
    } catch (error) {
      console.error('Error creating chat:', error)
    }
  }

  const deleteChat = async (chatId: number, e: React.MouseEvent) => {
    e.stopPropagation() // Предотвращаем открытие чата при клике на кнопку удаления
    
    if (!window.confirm('Вы уверены, что хотите удалить этот чат?')) {
      return
    }

    try {
      await api.delete(`/chats/${chatId}`)
      // Обновляем список чатов после удаления
      await loadChats()
    } catch (error) {
      console.error('Error deleting chat:', error)
      alert('Ошибка при удалении чата')
    }
  }

  return (
    <div className="chat-list-page">
      <header className="app-header">
        <h1>B24 Analytics Hub</h1>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate('/dashboards')}>
            Дашборды
          </button>
          {user?.is_admin && (
            <button className="btn btn-secondary" onClick={() => navigate('/admin')}>
              Админ-панель
            </button>
          )}
          <button className="btn btn-secondary" onClick={logout}>
            Выйти
          </button>
        </div>
      </header>

      <div className="chat-list-container">
        <div className="chat-list-header">
          <h2>Мои чаты</h2>
          <button className="btn btn-primary" onClick={() => setShowNewChat(true)}>
            Новый чат
          </button>
        </div>

        {showNewChat && (
          <div className="new-chat-form">
            <input
              type="text"
              placeholder="Название чата"
              value={newChatTitle}
              onChange={(e) => setNewChatTitle(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && createChat()}
            />
            <button className="btn btn-primary" onClick={createChat}>
              Создать
            </button>
            <button className="btn btn-secondary" onClick={() => setShowNewChat(false)}>
              Отмена
            </button>
          </div>
        )}

        {loading ? (
          <div className="loader"></div>
        ) : chats.length === 0 ? (
          <div className="empty-state">
            <p>У вас пока нет чатов. Создайте новый!</p>
          </div>
        ) : (
          <div className="chat-list">
            {chats.map((chat) => (
              <div
                key={chat.id}
                className="chat-item"
                onClick={() => navigate(`/chat/${chat.id}`)}
              >
                <div className="chat-item-content">
                  <h3>{chat.title}</h3>
                  <p className="chat-meta">
                    Токенов использовано: {chat.total_tokens}
                  </p>
                </div>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={(e) => deleteChat(chat.id, e)}
                  title="Удалить чат"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

