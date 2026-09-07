import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const isProduction = process.env.NODE_ENV === 'production'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8022',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    sourcemap: isProduction ? false : 'inline',
    minify: 'terser',
    terserOptions: {
      format: {
        comments: false,
      },
    },
  },
})
