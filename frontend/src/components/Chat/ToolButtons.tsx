import { useState, useEffect } from 'react'
import { api } from '../../services/api'
import { ToolMetadata } from '../../types'

interface ToolButtonsProps {
  chatId: number
  onToolResult: () => void
}

interface ParameterField {
  name: string
  type: string
  description?: string
  required?: boolean
  default?: any
  format?: string
  isDate?: boolean
}

export default function ToolButtons({ chatId, onToolResult }: ToolButtonsProps) {
  const [tools, setTools] = useState<ToolMetadata[]>([])
  const [selectedTool, setSelectedTool] = useState<ToolMetadata | null>(null)
  const [toolArgs, setToolArgs] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const response = await api.get<ToolMetadata[]>('/mcp/tools')
      // API already returns only popular tools
      setTools(response.data)
    } catch (error) {
      console.error('Error loading tools:', error)
    }
  }

  const isDateParameter = (name: string, type: string, format?: string, description?: string): boolean => {
    // Check format in JSON Schema
    if (format === 'date' || format === 'date-time') {
      return true
    }
    
    // Check parameter name for date-related keywords
    const nameLower = name.toLowerCase()
    const dateKeywords = ['date', 'time', 'created', 'updated', 'start', 'end', 'from', 'to']
    if (dateKeywords.some(keyword => nameLower.includes(keyword))) {
      return true
    }
    
    // Check description for date-related keywords
    if (description) {
      const descLower = description.toLowerCase()
      if (dateKeywords.some(keyword => descLower.includes(keyword))) {
        return true
      }
    }
    
    return false
  }

  const parseParameters = (params: any): ParameterField[] => {
    if (!params || typeof params !== 'object') {
      return []
    }
    
    // Handle JSON Schema format with properties
    if (params.properties && typeof params.properties === 'object') {
      const required = params.required || []
      return Object.keys(params.properties).map(name => {
        const prop = params.properties[name]
        let paramType = prop.type || 'string'
        
        // Handle array type
        if (prop.type === 'array') {
          paramType = 'array'
        }
        // Handle object type - check for object type or additionalProperties (which indicates object)
        else if (prop.type === 'object' || 
                 (prop.type === undefined && prop.properties) ||
                 prop.additionalProperties !== undefined) {
          paramType = 'object'
        }
        
        const isDate = isDateParameter(name, paramType, prop.format, prop.description)
        
        return {
          name,
          type: paramType,
          description: prop.description,
          required: required.includes(name),
          default: prop.default,
          format: prop.format,
          isDate
        }
      })
    }
    
    // Handle case where params is already an object with parameter names as keys
    // and values are parameter definitions (JSON Schema objects)
    const keys = Object.keys(params)
    if (keys.length > 0) {
      // Check if first value looks like a parameter definition (has type, default, etc.)
      const firstKey = keys[0]
      const firstValue = params[firstKey]
      
      if (firstValue && typeof firstValue === 'object' && 
          (firstValue.type !== undefined || firstValue.default !== undefined || firstValue.title !== undefined)) {
        // This is a format where each key is a parameter name and value is its schema
        return keys.map(name => {
          const prop = params[name]
          let paramType = prop.type || 'string'
          
          if (prop.type === 'array') {
            paramType = 'array'
          } else if (prop.type === 'object' || 
                     prop.additionalProperties !== undefined ||
                     (prop.type === undefined && prop.properties)) {
            paramType = 'object'
          }
          
          const isDate = isDateParameter(name, paramType, prop.format, prop.description || prop.title)
          
          return {
            name,
            type: paramType,
            description: prop.description || prop.title,
            required: false,
            default: prop.default,
            format: prop.format,
            isDate
          }
        })
      }
    }
    
    // Handle simple object format (direct parameter definitions)
    return Object.keys(params).map(name => {
      const value = params[name]
      let paramType = typeof value
      if (Array.isArray(value)) {
        paramType = 'array'
      } else if (value !== null && typeof value === 'object') {
        paramType = 'object'
      }
      
      const isDate = isDateParameter(name, paramType)
      
      return {
        name,
        type: paramType,
        description: undefined,
        required: false,
        default: value,
        isDate
      }
    })
  }

  const handleToolSelect = (tool: ToolMetadata) => {
    console.log('Selected tool:', tool)
    console.log('Tool parameters:', tool.parameters)
    setSelectedTool(tool)
    // Initialize args with defaults
    const params = parseParameters(tool.parameters)
    console.log('Parsed params:', params)
    const initialArgs: Record<string, any> = {}
    params.forEach(param => {
      if (param.default !== undefined && param.default !== null) {
        initialArgs[param.name] = param.default
      } else if (param.type === 'boolean') {
        initialArgs[param.name] = false
      } else if (param.isDate) {
        // Don't set default for date fields if not specified - leave undefined
      } else if (param.type === 'number' || param.type === 'integer') {
        // Don't set default for numbers if not specified - leave undefined
      } else if (param.type === 'array') {
        initialArgs[param.name] = []
      } else if (param.type === 'object') {
        // For objects, if default is null or undefined, use empty object
        if (param.default === null || param.default === undefined) {
          initialArgs[param.name] = {}
        } else {
          initialArgs[param.name] = param.default
        }
      } else {
        initialArgs[param.name] = ''
      }
    })
    console.log('Initial args:', initialArgs)
    setToolArgs(initialArgs)
  }

  const updateArg = (name: string, value: any) => {
    setToolArgs(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const callTool = async () => {
    if (!selectedTool) return

    try {
      setLoading(true)
      
      await api.post(`/chats/${chatId}/call-tool`, {
        server_name: selectedTool.server_name || 'bitrix24-main',
        tool_name: selectedTool.name,
        arguments: toolArgs
      })

      setSelectedTool(null)
      setToolArgs({})
      // Refresh messages to show the tool result
      onToolResult()
    } catch (error: any) {
      console.error('Error calling tool:', error)
      const errorMessage = error.response?.data?.detail || 'Ошибка при вызове инструмента'
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="tool-buttons">
      <h4>Быстрые инструменты:</h4>
      <div className="tool-list">
        {tools.map((tool) => (
          <button
            key={tool.name}
            className="btn btn-tool"
            onClick={() => handleToolSelect(tool)}
          >
            {tool.display_name || tool.name}
          </button>
        ))}
      </div>

      {selectedTool && (
        <div className="tool-modal">
          <div className="tool-modal-content">
            <h3>{selectedTool.display_name || selectedTool.name}</h3>
            <p>{selectedTool.display_description || selectedTool.description}</p>
            
            <div className="tool-parameters">
              <h4>Параметры:</h4>
              {(() => {
                const parsedParams = parseParameters(selectedTool.parameters)
                console.log('Rendering parameters:', parsedParams)
                return parsedParams.length > 0 ? (
                  parsedParams.map((param) => (
                  <div key={param.name} className="parameter-field">
                    <label htmlFor={`param-${param.name}`}>
                      {param.name}
                      {param.required && <span className="required">*</span>}
                    </label>
                    {param.description && (
                      <div className="param-description">{param.description}</div>
                    )}
                    {param.type === 'boolean' ? (
                      <div className="checkbox-wrapper">
                        <input
                          id={`param-${param.name}`}
                          type="checkbox"
                          checked={toolArgs[param.name] === true}
                          onChange={(e) => updateArg(param.name, e.target.checked)}
                        />
                        <span>{toolArgs[param.name] ? 'Да' : 'Нет'}</span>
                      </div>
                    ) : param.isDate ? (
                      <input
                        id={`param-${param.name}`}
                        type="date"
                        value={
                          toolArgs[param.name] 
                            ? (typeof toolArgs[param.name] === 'string' 
                                ? toolArgs[param.name].split('T')[0] 
                                : String(toolArgs[param.name]).split('T')[0])
                            : ''
                        }
                        onChange={(e) => {
                          const dateValue = e.target.value || undefined
                          updateArg(param.name, dateValue)
                        }}
                      />
                    ) : param.type === 'number' || param.type === 'integer' ? (
                      <input
                        id={`param-${param.name}`}
                        type="number"
                        value={toolArgs[param.name] !== undefined && toolArgs[param.name] !== null ? toolArgs[param.name] : ''}
                        onChange={(e) => {
                          const value = e.target.value === '' 
                            ? (param.default !== undefined ? param.default : undefined)
                            : (param.type === 'integer' ? parseInt(e.target.value) || 0 : parseFloat(e.target.value) || 0)
                          updateArg(param.name, value)
                        }}
                        placeholder={param.default !== undefined ? String(param.default) : ''}
                      />
                    ) : param.type === 'array' || param.type === 'object' ? (
                      <textarea
                        id={`param-${param.name}`}
                        value={
                          toolArgs[param.name] !== undefined && toolArgs[param.name] !== null
                            ? JSON.stringify(toolArgs[param.name], null, 2)
                            : ''
                        }
                        onChange={(e) => {
                          try {
                            const parsed = e.target.value.trim() === '' 
                              ? (param.type === 'array' ? [] : {})
                              : JSON.parse(e.target.value)
                            updateArg(param.name, parsed)
                          } catch {
                            // Invalid JSON, keep as is
                          }
                        }}
                        placeholder={param.type === 'array' ? '[]' : '{}'}
                        rows={4}
                        className="json-input"
                      />
                    ) : (
                      <input
                        id={`param-${param.name}`}
                        type="text"
                        value={
                          typeof toolArgs[param.name] === 'object' && toolArgs[param.name] !== null
                            ? JSON.stringify(toolArgs[param.name])
                            : (toolArgs[param.name] !== undefined && toolArgs[param.name] !== null ? String(toolArgs[param.name]) : '')
                        }
                        onChange={(e) => {
                          // Try to parse as JSON if it looks like JSON
                          const value = e.target.value
                          if (value.trim().startsWith('{') || value.trim().startsWith('[')) {
                            try {
                              updateArg(param.name, JSON.parse(value))
                            } catch {
                              updateArg(param.name, value)
                            }
                          } else {
                            updateArg(param.name, value)
                          }
                        }}
                        placeholder={param.default !== undefined && param.default !== null ? String(param.default) : 'Введите значение'}
                      />
                    )}
                  </div>
                  ))
                ) : (
                  <p className="no-parameters">Этот инструмент не требует параметров</p>
                )
              })()}
            </div>

            <div className="tool-modal-actions">
              <button
                className="btn btn-primary"
                onClick={callTool}
                disabled={loading}
              >
                {loading ? 'Выполнение...' : 'Выполнить'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setSelectedTool(null)
                  setToolArgs({})
                }}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

