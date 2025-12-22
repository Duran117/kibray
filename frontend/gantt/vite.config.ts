import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Replace process.env.NODE_ENV for browser compatibility
    'process.env.NODE_ENV': JSON.stringify('production'),
    'process.env': JSON.stringify({}),
  },
  build: {
    // Output to Django static folder
    outDir: '../../static/gantt',
    emptyOutDir: true,
    // Use rollup for a single bundle
    rollupOptions: {
      input: resolve(__dirname, 'src/main-django.tsx'),
      output: {
        // Single IIFE file
        format: 'iife',
        entryFileNames: 'gantt-app.iife.js',
        // Ensure CSS is bundled
        assetFileNames: 'assets/[name][extname]',
        // Single file output
        inlineDynamicImports: true,
      },
    },
  },
})
