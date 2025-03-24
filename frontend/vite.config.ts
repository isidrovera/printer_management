// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api/v1': {
        target: 'https://copierconnectremote.com',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🔴 proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('🔄 Proxy Request:', {
              method: req.method,
              url: req.url,
              targetUrl: proxyReq.path
            });
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('✅ Proxy Response:', {
              statusCode: proxyRes.statusCode,
              url: req.url
            });
          });
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  }
})