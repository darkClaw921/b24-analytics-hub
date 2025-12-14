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
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
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
      'determined_shockley.orb.local'
    ],
  },
})

