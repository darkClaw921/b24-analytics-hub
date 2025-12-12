import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { MCPTool } from '../../types'

export default function ToolSettings() {
  const [tools, setTools] = useState<MCPTool[]>([])
  const [editingTool, setEditingTool] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const response = await api.get<MCPTool[]>('/api/admin/mcp/tools')
      setTools(response.data)
    } catch (error) {
      console.error('Error loading tools:', error)
    }
  }

  const toggleActive = async (id: number, isActive: boolean) => {
    try {
      await api.put(`/api/admin/mcp/tools/${id}`, { is_active: !isActive })
      loadTools()
    } catch (error) {
      alert('Ошибка обновления инструмента')
    }
  }

  const togglePopular = async (id: number, isPopular: boolean) => {
    try {
      await api.put(`/api/admin/mcp/tools/${id}`, { is_popular: !isPopular })
      loadTools()
    } catch (error) {
      alert('Ошибка обновления инструмента')
    }
  }

  const startEdit = (tool: MCPTool) => {
    setEditingTool(tool.id)
    setEditName(tool.custom_name || '')
    setEditDescription(tool.custom_description || '')
  }

  const cancelEdit = () => {
    setEditingTool(null)
    setEditName('')
    setEditDescription('')
  }

  const saveEdit = async (id: number) => {
    try {
      await api.put(`/api/admin/mcp/tools/${id}`, {
        custom_name: editName.trim() || null,
        custom_description: editDescription.trim() || null
      })
      setEditingTool(null)
      setEditName('')
      setEditDescription('')
      loadTools()
    } catch (error) {
      alert('Ошибка сохранения изменений')
    }
  }

  return (
    <div className="tool-settings">
      <h2>Управление инструментами</h2>
      <p style={{ marginBottom: '20px', color: '#666' }}>
        Кастомное имя и описание используются только для визуального отображения в быстрых инструментах
      </p>

      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Имя инструмента</th>
            <th>Описание</th>
            <th>Кастомное имя</th>
            <th>Кастомное описание</th>
            <th>Активен</th>
            <th>Популярный</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {tools.map((tool) => (
            <tr key={tool.id}>
              <td>{tool.id}</td>
              <td>{tool.tool_name}</td>
              <td>{tool.tool_description || '-'}</td>
              <td>
                {editingTool === tool.id ? (
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder={tool.tool_name}
                    style={{ width: '100%', padding: '5px' }}
                  />
                ) : (
                  <span>{tool.custom_name || '-'}</span>
                )}
              </td>
              <td>
                {editingTool === tool.id ? (
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    placeholder={tool.tool_description || ''}
                    style={{ width: '100%', padding: '5px', minHeight: '60px' }}
                  />
                ) : (
                  <span>{tool.custom_description || '-'}</span>
                )}
              </td>
              <td>
                <button
                  className={`btn ${tool.is_active ? 'btn-success' : 'btn-secondary'}`}
                  onClick={() => toggleActive(tool.id, tool.is_active)}
                  disabled={editingTool === tool.id}
                >
                  {tool.is_active ? 'Активен' : 'Неактивен'}
                </button>
              </td>
              <td>
                <button
                  className={`btn ${tool.is_popular ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => togglePopular(tool.id, tool.is_popular)}
                  disabled={editingTool === tool.id}
                >
                  {tool.is_popular ? '⭐' : '☆'}
                </button>
              </td>
              <td>
                {editingTool === tool.id ? (
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <button
                      className="btn btn-success"
                      onClick={() => saveEdit(tool.id)}
                      style={{ fontSize: '12px', padding: '5px 10px' }}
                    >
                      Сохранить
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={cancelEdit}
                      style={{ fontSize: '12px', padding: '5px 10px' }}
                    >
                      Отмена
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn btn-primary"
                    onClick={() => startEdit(tool)}
                    style={{ fontSize: '12px', padding: '5px 10px' }}
                  >
                    Редактировать
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

