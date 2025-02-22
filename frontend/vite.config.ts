import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/clients': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/monitor': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/printer-oids': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/agents': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/drivers': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/tunnels': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})