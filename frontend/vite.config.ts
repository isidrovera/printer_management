// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://161.132.39.159:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://161.132.39.159:8000',
        ws: true,
      }
    },
    cors: true,
    hmr: {
      host: '161.132.39.159',
      port: 3000,
      protocol: 'ws'
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})