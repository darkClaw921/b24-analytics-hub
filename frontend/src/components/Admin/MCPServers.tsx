import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { MCPServer } from '../../types'

export default function MCPServers() {
  const [servers, setServers] = useState<MCPServer[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    transport: 'streamable_http' as const,
    auth_token: '',
    is_active: true
  })

  useEffect(() => {
    loadServers()
  }, [])

  const loadServers = async () => {
    try {
      const response = await api.get<MCPServer[]>('/admin/mcp/servers')
      setServers(response.data)
    } catch (error) {
      console.error('Error loading servers:', error)
    }
  }

  const resetForm = () => {
    setFormData({ name: '', url: '', transport: 'streamable_http', auth_token: '', is_active: true })
    setEditingId(null)
    setShowForm(false)
  }

  const startEdit = (server: MCPServer) => {
    setFormData({
      name: server.name,
      url: server.url,
      transport: server.transport,
      auth_token: '', // Не показываем токен при редактировании из соображений безопасности
      is_active: server.is_active
    })
    setEditingId(server.id)
    setShowForm(true)
  }

  const createServer = async () => {
    try {
      await api.post('/admin/mcp/servers', formData)
      resetForm()
      loadServers()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Ошибка создания сервера')
    }
  }

  const updateServer = async () => {
    if (!editingId) return
    try {
      await api.put(`/admin/mcp/servers/${editingId}`, formData)
      resetForm()
      loadServers()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Ошибка обновления сервера')
    }
  }

  const handleSubmit = () => {
    if (editingId) {
      updateServer()
    } else {
      createServer()
    }
  }

  const toggleActive = async (id: number, isActive: boolean) => {
    try {
      await api.put(`/admin/mcp/servers/${id}`, { is_active: !isActive })
      loadServers()
    } catch (error) {
      alert('Ошибка обновления сервера')
    }
  }

  const deleteServer = async (id: number) => {
    if (!confirm('Удалить сервер?')) return
    try {
      await api.delete(`/admin/mcp/servers/${id}`)
      loadServers()
    } catch (error) {
      alert('Ошибка удаления сервера')
    }
  }

  return (
    <div className="mcp-servers">
      <h2>Управление MCP серверами</h2>
      
      <button className="btn btn-primary" onClick={() => setShowForm(true)}>
        Добавить сервер
      </button>

      {showForm && (
        <div className="server-form">
          <h3>{editingId ? 'Редактировать сервер' : 'Добавить сервер'}</h3>
          <input
            type="text"
            placeholder="Имя сервера"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <input
            type="url"
            placeholder="URL"
            value={formData.url}
            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          />
          <select
            value={formData.transport}
            onChange={(e) => setFormData({ ...formData, transport: e.target.value as 'streamable_http' | 'stdio' | 'sse' })}
          >
            <option value="streamable_http">streamable_http</option>
            <option value="stdio">stdio</option>
            <option value="sse">sse</option>
          </select>
          <input
            type="text"
            placeholder="Auth Token (опционально)"
            value={formData.auth_token}
            onChange={(e) => setFormData({ ...formData, auth_token: e.target.value })}
          />
          <label>
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
            />
            Активен
          </label>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={handleSubmit}>
              {editingId ? 'Сохранить' : 'Создать'}
            </button>
            <button className="btn btn-secondary" onClick={resetForm}>Отмена</button>
          </div>
        </div>
      )}

      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>URL</th>
            <th>Транспорт</th>
            <th>Активен</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {servers.map((server) => (
            <tr key={server.id}>
              <td>{server.id}</td>
              <td>{server.name}</td>
              <td>{server.url}</td>
              <td>{server.transport}</td>
              <td>
                <button
                  className={`btn ${server.is_active ? 'btn-success' : 'btn-secondary'}`}
                  onClick={() => toggleActive(server.id, server.is_active)}
                >
                  {server.is_active ? 'Активен' : 'Неактивен'}
                </button>
              </td>
              <td>
                <button 
                  className="btn btn-primary" 
                  onClick={() => startEdit(server)}
                  style={{ marginRight: '8px' }}
                >
                  Редактировать
                </button>
                <button className="btn btn-danger" onClick={() => deleteServer(server.id)}>
                  Удалить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

