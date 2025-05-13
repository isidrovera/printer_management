// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// Función de utilidad para guardar logs de solicitudes en un archivo para depuración
const createLogger = () => {
  const logFile = path.resolve(__dirname, 'proxy-debug.log')
  
  // Limpiar archivo de log al iniciar
  if (fs.existsSync(logFile)) {
    fs.writeFileSync(logFile, '', 'utf8')
  }
  
  return {
    log: (message, data) => {
      const timestamp = new Date().toISOString()
      const logEntry = `[${timestamp}] ${message}: ${JSON.stringify(data, null, 2)}\n`
      
      console.log(logEntry)
      fs.appendFileSync(logFile, logEntry, 'utf8')
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
            const errDetails = {
              message: err.message,
              stack: err.stack,
              url: req.url,
              method: req.method,
              headers: req.headers
            }
            logger.log('🔴 Error en proxy', errDetails)
            
            // Si es posible, escribe información de error en la respuesta
            if (!res.headersSent) {
              res.writeHead(500, {
                'Content-Type': 'application/json'
              })
            }
            
            const body = { error: 'Proxy error', details: err.message }
            res.end(JSON.stringify(body))
          })
          
          // Log antes de enviar la solicitud proxy
          proxy.on('proxyReq', (proxyReq, req, res) => {
            const reqDetails = {
              method: req.method,
              url: req.url,
              headers: req.headers,
              targetUrl: proxyReq.path,
              protocol: proxyReq.protocol,
              host: proxyReq.host,
              fullUrl: `${proxyReq.protocol}//${proxyReq.host}${proxyReq.path}`
            }
            
            // Verificar si hay cambio de protocolo
            if (req.url.includes('http:')) {
              logger.log('⚠️ ALERTA: URL con HTTP detectada en solicitud', { url: req.url })
            }
            
            if (proxyReq.path.includes('http:')) {
              logger.log('⚠️ ALERTA: Path con HTTP detectado en proxy', { path: proxyReq.path })
            }
            
            // Intento de forzar HTTPS en la solicitud proxy
            if (proxyReq.protocol === 'http:') {
              logger.log('🛑 ALERTA CRÍTICA: Protocolo HTTP detectado en proxy', { 
                before: proxyReq.protocol,
                path: proxyReq.path
              })
              // Nota: No podemos cambiar el protocolo directamente aquí,
              // pero este log nos ayudará a identificar el problema
            }
            
            logger.log('🔄 Solicitud Proxy', reqDetails)
          })
          
          // Log después de recibir la respuesta
          proxy.on('proxyRes', (proxyRes, req, res) => {
            const resDetails = {
              statusCode: proxyRes.statusCode,
              headers: proxyRes.headers,
              url: req.url,
              method: req.method
            }
            
            // Verificar redirecciones
            if (proxyRes.statusCode >= 300 && proxyRes.statusCode < 400) {
              logger.log('⚠️ Redirección detectada', {
                status: proxyRes.statusCode,
                location: proxyRes.headers.location,
                originalUrl: req.url
              })
              
              // Verificar si la redirección cambia HTTPS a HTTP
              if (proxyRes.headers.location && 
                  proxyRes.headers.location.startsWith('http:')) {
                logger.log('🛑 ALERTA CRÍTICA: Redirección a HTTP', {
                  location: proxyRes.headers.location,
                  originalUrl: req.url
                })
                
                // Intentar forzar HTTPS en la redirección
                // Nota: Este es un log, no cambia realmente la redirección
                logger.log('Intento de corrección', {
                  original: proxyRes.headers.location,
                  corregido: proxyRes.headers.location.replace('http:', 'https:')
                })
              }
            }
            
            logger.log('✅ Respuesta Proxy', resDetails)
          })
          
          // Log cuando la conexión se establece
          proxy.on('start', (req, res) => {
            logger.log('🚀 Iniciando proxy', {
              url: req.url,
              method: req.method
            })
          })
          
          // Log cuando la conexión termina
          proxy.on('end', (req, res) => {
            logger.log('🏁 Finalizando proxy', {
              url: req.url,
              method: req.method,
              statusCode: res.statusCode
            })
          })
        },
        // Intentar forzar HTTPS en vez de HTTP
        protocolRewrite: 'https',
        // Logs detallados
        logLevel: 'debug'
      }
    },
    // Logs detallados del servidor
    middlewareMode: 'ssr',
    hmr: {
      protocol: 'wss',
      clientPort: 443,
      overlay: true
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Configuración de logs adicionales de Vite
  logLevel: 'info',
  clearScreen: false,
  // Forzar HTTPS en todas las solicitudes
  optimizeDeps: {
    entries: ['./src/main.tsx'],
    force: true
  },
  // Manejadores de eventos adicionales para depuración
  build: {
    target: 'es2015',
    outDir: 'dist',
    rollupOptions: {
      onwarn: (warning, warn) => {
        // Log de advertencias de construcción
        console.warn(`[BUILD WARNING] ${warning.message}`)
        warn(warning)
      }
    }
  }
})