import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: Vite serves the SPA and proxies /api to Django (runserver on :8000).
// Build: emit into backend/frontend_dist so Django/WhiteNoise serve the SPA (one container).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: '../backend/frontend_dist',
    emptyOutDir: true,
  },
})
