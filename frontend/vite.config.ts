// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// Función para registrar logs
const createLogger = () => {
  const logFile = path.resolve(__dirname, 'proxy-debug.log')
  
  // Limpiar archivo de log al iniciar
  try {
    fs.writeFileSync(logFile, '', 'utf8')
  } catch (error) {
    console.error('Error al crear archivo de log:', error)
  }
  
  return {
    log: (message, data) => {
      const timestamp = new Date().toISOString()
      const logEntry = `[${timestamp}] ${message}: ${JSON.stringify(data, null, 2)}\n`
      
      console.log(logEntry)
      try {
        fs.appendFileSync(logFile, logEntry, 'utf8')
      } catch (error) {
        console.error('Error al escribir en archivo de log:', error)
      }
    }
  }
}

const logger = createLogger()

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['mps.copierconnectremote.com'],
    proxy: {
      '/api/v1': {
        target: 'https://copierconnectremote.com',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => {
          const newPath = path.replace(/^\/api\/v1/, '/api/v1')
          logger.log('Proxy rewrite', { 
            originalPath: path, 
            newPath: newPath
          })
          return newPath
        },
        configure: (proxy, _options) => {
          // Log cada vez que el proxy es configurado
          logger.log('Proxy configurado', { 
            target: 'https://copierconnectremote.com',
            options: JSON.stringify(_options)
          })
          
          // Manejar errores de proxy
          proxy.on('error', (err, req, res) => {
            logger.log('Error en proxy', {
              message: err.message,
              url: req.url,
              method: req.method
            })
          })
          
          // Log de solicitud proxy
          proxy.on('proxyReq', (proxyReq, req, res) => {
            logger.log('Solicitud Proxy', {
              method: req.method,
              url: req.url,
              targetUrl: proxyReq.path
            })
          })
          
          // Log de respuesta proxy
          proxy.on('proxyRes', (proxyRes, req, res) => {
            logger.log('Respuesta Proxy', {
              statusCode: proxyRes.statusCode,
              url: req.url,
              method: req.method
            })
          })
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