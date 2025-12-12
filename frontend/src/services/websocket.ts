const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001'

export class WebSocketService {
  private ws: WebSocket | null = null
  private chatId: number | null = null

  connect(chatId: number, onMessage: (data: any) => void) {
    this.chatId = chatId
    this.ws = new WebSocket(`${WS_URL}/ws/chats/${chatId}`)

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
      console.error('WebSocket error:', error)
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

