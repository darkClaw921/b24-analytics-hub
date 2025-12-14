import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    hmr: {
      // Автоматическое определение host и protocol из заголовков запроса
      // Поддерживает оба домена:
      // - b24analitycshub-frontend-wc7d9n-cad79c-45-84-227-231.traefik.me (wss)
      // - b24-analytics-frontend.orb.local (ws)
      // Протокол определяется автоматически на основе текущего соединения
    },
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8001',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_BACKEND_URL || 'ws://localhost:8001',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: [
      'b24analitycshub-frontend-wc7d9n-cad79c-45-84-227-231.traefik.me',
      'b24-analytics-frontend.orb.local',
      '*.orb.local',
      'determined_shockley.orb.local',
      'b24-analytics-hub-frontend.b24-analytics-hub.orb.local'
    ],
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8001',
        changeOrigin: true,
      },
      '/ws': {
        target: (process.env.VITE_BACKEND_URL || 'http://localhost:8001')?.replace('http', 'ws'),
        ws: true,
        changeOrigin: true,
      },
    },
  },
})

