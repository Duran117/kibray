import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/static/gantt/',
  build: {
    outDir: '../staticfiles/gantt',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: './src/main.tsx'
      },
      output: {
        entryFileNames: 'gantt.[hash].js',
        chunkFileNames: 'gantt.[hash].js',
        assetFileNames: 'gantt.[hash].[ext]'
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
