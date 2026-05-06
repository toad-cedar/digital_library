import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss()
  ],
  server: {
    proxy: {
      // Проксирует все запросы, начинающиеся с /api, на бэкенд
      '/api': {
        target: 'http://localhost:8000', // Адрес uvicorn
        changeOrigin: true
      },
    },
  },
})
