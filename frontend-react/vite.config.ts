import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), '')
  
  // Use VITE_API_URL from env, fallback to localhost:8000 for local dev
  const apiUrl = env.VITE_API_URL || 'http://localhost:8000'
  
  return {
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
          target: apiUrl,
          changeOrigin: true,
        },
        '/accounts': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/consents': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/payments': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/payment-consents': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/account-consents': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/banker': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/admin': {
          target: apiUrl,
          changeOrigin: true,
        },
        '/api': {
          target: apiUrl,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: '0.0.0.0',
      port: 3000,
      allowedHosts: true
    },
  }
})

