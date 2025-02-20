import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Permitir acceso desde IP externa
    port: 3000, // Puerto específico
    strictPort: true, // Usar estrictamente este puerto
  },
})