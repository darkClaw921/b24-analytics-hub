// Определяем протокол WebSocket на основе текущего протокола страницы
const getWebSocketUrl = () => {
  // Если указан явный URL для WebSocket, используем его
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }
  
  // Если есть URL бэкенда, используем его для WebSocket
  const backendUrl = import.meta.env.VITE_BACKEND_URL
  if (backendUrl && !backendUrl.startsWith('/')) {
    // Абсолютный URL - преобразуем http -> ws, https -> wss
    const wsUrl = backendUrl.replace(/^http/, 'ws').replace(/^https/, 'wss')
    return `${wsUrl}/ws`
  }
  
  // Иначе используем относительный путь через proxy
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/ws`
}

const WS_URL = getWebSocketUrl()

export class WebSocketService {
  private ws: WebSocket | null = null
  private chatId: number | null = null

  connect(chatId: number, onMessage: (data: any) => void) {
    this.chatId = chatId
    this.ws = new WebSocket(`${WS_URL}/chats/${chatId}`)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    this.ws.onerror = (error) => {
      // Логируем ошибки только в режиме разработки
      if (import.meta.env.DEV) {
        console.error('WebSocket error:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.chatId = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const wsService = new WebSocketService()

