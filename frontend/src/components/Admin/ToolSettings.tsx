import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { MCPTool } from '../../types'

interface ExpandableDescriptionProps {
  text: string | null
  maxLength?: number
}

function ExpandableDescription({ text, maxLength = 80 }: ExpandableDescriptionProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  if (!text || text === '-') {
    return <span>-</span>
  }

  // Проверяем, нужно ли обрезать текст (примерно 2 строки)
  const shouldTruncate = text.length > maxLength

  if (!shouldTruncate) {
    return <span>{text}</span>
  }

  return (
    <div className={`expandable-description ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <span className="expandable-description-text">{text}</span>
      <span 
        className="expand-toggle"
        onClick={(e) => {
          e.stopPropagation()
          setIsExpanded(!isExpanded)
        }}
      >
        {isExpanded ? ' Свернуть' : ' Показать больше'}
      </span>
    </div>
  )
}

export default function ToolSettings() {
  const [tools, setTools] = useState<MCPTool[]>([])
  const [editingTool, setEditingTool] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editingParametersTool, setEditingParametersTool] = useState<number | null>(null)
  const [toolParameters, setToolParameters] = useState<Record<string, any>>({})
  const [parameterDisplayNames, setParameterDisplayNames] = useState<Record<string, string>>({})
  const [hiddenParameters, setHiddenParameters] = useState<string[]>([])
  const [loadingParameters, setLoadingParameters] = useState(false)

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const response = await api.get<MCPTool[]>('/admin/mcp/tools')
      setTools(response.data)
    } catch (error) {
      console.error('Error loading tools:', error)
    }
  }

  const toggleActive = async (id: number, isActive: boolean) => {
    try {
      await api.put(`/admin/mcp/tools/${id}`, { is_active: !isActive })
      loadTools()
    } catch (error) {
      alert('Ошибка обновления инструмента')
    }
  }

  const togglePopular = async (id: number, isPopular: boolean) => {
    try {
      await api.put(`/admin/mcp/tools/${id}`, { is_popular: !isPopular })
      loadTools()
    } catch (error) {
      alert('Ошибка обновления инструмента')
    }
  }

  const startEdit = async (tool: MCPTool) => {
    setEditingTool(tool.id)
    setEditName(tool.custom_name || '')
    setEditDescription(tool.custom_description || '')
  }

  const cancelEdit = () => {
    setEditingTool(null)
    setEditName('')
    setEditDescription('')
  }

  const parseParametersSchema = (paramsSchema: any): Record<string, any> => {
    if (!paramsSchema || typeof paramsSchema !== 'object') {
      console.log('parseParametersSchema: paramsSchema is not an object', paramsSchema)
      return {}
    }
    
    // Handle JSON Schema format with properties
    // Format: {type: "object", properties: {...}}
    if (paramsSchema.properties && typeof paramsSchema.properties === 'object') {
      console.log('parseParametersSchema: Found properties in schema', Object.keys(paramsSchema.properties))
      return paramsSchema.properties
    }
    
    // Handle case where paramsSchema is already a properties object
    // Format: {param1: {type: "string", ...}, param2: {type: "number", ...}}
    const keys = Object.keys(paramsSchema)
    if (keys.length > 0) {
      // Check if first value looks like a parameter definition (has type, default, etc.)
      const firstKey = keys[0]
      const firstValue = paramsSchema[firstKey]
      
      if (firstValue && typeof firstValue === 'object' && 
          (firstValue.type !== undefined || firstValue.default !== undefined || firstValue.title !== undefined || firstValue.description !== undefined)) {
        // This is already a properties object
        console.log('parseParametersSchema: Schema is already a properties object', keys)
        return paramsSchema
      }
    }
    
    // Check if it's an empty object
    if (keys.length === 0) {
      console.log('parseParametersSchema: Empty schema object')
      return {}
    }
    
    // If it doesn't match patterns, log and return empty
    console.log('parseParametersSchema: Unknown schema format', paramsSchema)
    return {}
  }

  const startEditParameters = async (tool: MCPTool) => {
    setEditingParametersTool(tool.id)
    setParameterDisplayNames(tool.parameter_display_names || {})
    setHiddenParameters(tool.hidden_parameters || [])
    setLoadingParameters(true)
    setToolParameters({})
    
    // Load tool parameters
    try {
      const response = await api.get<{ parameters: Record<string, any> }>(`/admin/mcp/tools/${tool.id}/parameters`)
      console.log('Parameters response:', response.data)
      
      const paramsSchema = response.data.parameters
      if (!paramsSchema || (typeof paramsSchema === 'object' && Object.keys(paramsSchema).length === 0)) {
        console.warn('No parameters in response or empty object')
        setToolParameters({})
        setLoadingParameters(false)
        return
      }
      
      // Parse parameters schema using the same logic as ToolButtons
      const params = parseParametersSchema(paramsSchema)
      
      console.log('Parsed parameters:', params)
      console.log('Parameters count:', Object.keys(params).length)
      console.log('Parameters keys:', Object.keys(params))
      
      if (Object.keys(params).length === 0) {
        console.warn('No parameters found after parsing')
        console.warn('Original schema:', paramsSchema)
      }
      
      setToolParameters(params)
    } catch (error: any) {
      console.error('Error loading tool parameters:', error)
      console.error('Error details:', error.response?.data)
      setToolParameters({})
    } finally {
      setLoadingParameters(false)
    }
  }

  const cancelEditParameters = () => {
    setEditingParametersTool(null)
    setToolParameters({})
    setParameterDisplayNames({})
    setHiddenParameters([])
    setLoadingParameters(false)
  }

  const updateParameterDisplayName = (originalName: string, displayName: string) => {
    setParameterDisplayNames(prev => {
      const trimmed = displayName.trim()
      const updated = { ...prev }
      if (trimmed) {
        updated[originalName] = trimmed  // trim only removes leading/trailing spaces, preserves internal spaces
      } else {
        delete updated[originalName]
      }
      return updated
    })
  }

  const toggleHiddenParameter = (paramName: string) => {
    setHiddenParameters(prev => {
      if (prev.includes(paramName)) {
        return prev.filter(p => p !== paramName)
      } else {
        return [...prev, paramName]
      }
    })
  }

  const saveEdit = async (id: number) => {
    try {
      await api.put(`/admin/mcp/tools/${id}`, {
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

  const saveParameters = async (id: number) => {
    try {
      // Remove empty display names (only trim leading/trailing spaces, preserve internal spaces)
      const cleanedDisplayNames: Record<string, string> = {}
      Object.entries(parameterDisplayNames).forEach(([key, value]) => {
        if (value && typeof value === 'string' && value.trim().length > 0) {
          // Only trim leading/trailing spaces, preserve all internal spaces
          cleanedDisplayNames[key] = value.trim()
        }
      })
      
      await api.put(`/admin/mcp/tools/${id}`, {
        parameter_display_names: Object.keys(cleanedDisplayNames).length > 0 ? cleanedDisplayNames : null,
        hidden_parameters: hiddenParameters.length > 0 ? hiddenParameters : null
      })
      setEditingParametersTool(null)
      setToolParameters({})
      setParameterDisplayNames({})
      setHiddenParameters([])
      loadTools()
    } catch (error) {
      alert('Ошибка сохранения параметров')
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
            <>
              <tr key={tool.id}>
                <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>{tool.id}</td>
                <td style={{ maxWidth: '200px' }}>{tool.tool_name}</td>
                <td className="description-cell">
                  <ExpandableDescription text={tool.tool_description} />
                </td>
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
                <td className="description-cell">
                  {editingTool === tool.id ? (
                    <textarea
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder={tool.tool_description || ''}
                      style={{ width: '100%', padding: '5px', minHeight: '60px' }}
                    />
                  ) : (
                    <ExpandableDescription text={tool.custom_description} />
                  )}
                </td>
                <td className="action-cell">
                  <button
                    className={`btn ${tool.is_active ? 'btn-success' : 'btn-secondary'}`}
                    onClick={() => toggleActive(tool.id, tool.is_active)}
                    disabled={editingTool === tool.id}
                  >
                    {tool.is_active ? 'Активен' : 'Неактивен'}
                  </button>
                </td>
                <td className="action-cell">
                  <button
                    className={`btn ${tool.is_popular ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => togglePopular(tool.id, tool.is_popular)}
                    disabled={editingTool === tool.id}
                  >
                    {tool.is_popular ? '⭐' : '☆'}
                  </button>
                </td>
                <td className="action-cell">
                  <div style={{ display: 'flex', gap: '5px', flexDirection: 'column', alignItems: 'center' }}>
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
                      <>
                        <button
                          className="btn btn-primary"
                          onClick={() => startEdit(tool)}
                          style={{ fontSize: '12px', padding: '5px 10px', width: '100%' }}
                        >
                          Редактировать
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => startEditParameters(tool)}
                          style={{ fontSize: '12px', padding: '5px 10px', width: '100%' }}
                        >
                          Параметры
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            </>
          ))}
        </tbody>
      </table>

      {/* Modal for editing parameters */}
      {editingParametersTool !== null && (
        <div className="modal-overlay" onClick={cancelEditParameters}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Редактирование параметров инструмента</h3>
              <button className="modal-close" onClick={cancelEditParameters}>×</button>
            </div>
            <div className="modal-body">
              {loadingParameters ? (
                <div className="no-parameters-message">
                  Загрузка параметров...
                </div>
              ) : Object.keys(toolParameters).length > 0 ? (
                <div className="parameters-edit-grid">
                  {Object.entries(toolParameters).map(([paramName, paramInfo]) => (
                    <div key={paramName} className="parameter-edit-item">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <label className="parameter-label">
                          <span className="parameter-original">Оригинальное название:</span>
                          <strong>{paramName}</strong>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={hiddenParameters.includes(paramName)}
                            onChange={() => toggleHiddenParameter(paramName)}
                          />
                          <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Скрыть</span>
                        </label>
                      </div>
                      {paramInfo && typeof paramInfo === 'object' && paramInfo.description && (
                        <div className="parameter-description">{paramInfo.description}</div>
                      )}
                      <input
                        type="text"
                        value={parameterDisplayNames[paramName] || ''}
                        onChange={(e) => updateParameterDisplayName(paramName, e.target.value)}
                        placeholder={`Введите визуальное название для ${paramName}`}
                        className="parameter-input"
                        disabled={hiddenParameters.includes(paramName)}
                        style={{ opacity: hiddenParameters.includes(paramName) ? 0.5 : 1 }}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-parameters-message">
                  Параметры не найдены. Возможно, этот инструмент не имеет параметров или произошла ошибка при загрузке.
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={cancelEditParameters}
              >
                Отмена
              </button>
              <button
                className="btn btn-success"
                onClick={() => saveParameters(editingParametersTool)}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

