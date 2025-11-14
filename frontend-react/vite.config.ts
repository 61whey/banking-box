import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/auth': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/accounts': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/consents': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/payments': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/payment-consents': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/account-consents': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/banker': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:54080',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
})

