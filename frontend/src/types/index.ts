export interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
}

export interface Chat {
  id: number
  title: string
  created_at: string
  updated_at: string
  total_tokens: number
}

export interface Message {
  id: number
  role: 'user' | 'assistant' | 'tool'
  content: string
  tool_name?: string
  tokens_used: number
  created_at: string
}

export interface MCPServer {
  id: number
  name: string
  url: string
  transport: 'streamable_http' | 'stdio' | 'sse'
  is_active: boolean
}

export interface MCPTool {
  id: number
  server_id: number
  tool_name: string
  tool_description?: string
  custom_name?: string
  custom_description?: string
  parameter_display_names?: Record<string, string>  // {"original_param": "display_name"}
  is_active: boolean
  is_popular: boolean
}

export interface ToolMetadata {
  name: string  // Реальное имя инструмента (используется для вызова)
  description: string  // Реальное описание инструмента
  display_name?: string  // Кастомное имя для визуального отображения
  display_description?: string  // Кастомное описание для визуального отображения
  parameters: Record<string, any>
  parameter_display_names?: Record<string, string>  // {"original_param": "display_name"}
  server_name?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface MessageResponse {
  message: string
  tokens_used: number
  tool_calls: boolean
}

