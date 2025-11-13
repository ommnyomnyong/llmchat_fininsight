import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 프론트에서 '/agent-call'로 요청하면 백엔드(8000)으로 자동 전달
      '/agent-call': {
        target: 'http://223.130.156.200:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

