import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname, '.'),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
      onwarn(warning, defaultHandler) {
        if (warning.code !== 'UNRESOLVED_IMPORT') {
          defaultHandler(warning);
        }
      },
    },
    commonjsOptions: {
      include: [/lucide-react/, /node_modules/],
    },
  },
  optimizeDeps: {
    include: ['lucide-react'],
  },
})