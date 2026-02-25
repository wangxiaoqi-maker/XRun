import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['legacy-js-api'], // 静默 Sass 弃用警告
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // Sonic Server 代理 - 指向云端
      '/sonic': {
        target: 'http://113.249.104.59:3001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/sonic/, '')
      },
      // iOS WDA 代理
      '/wda': {
        target: 'http://localhost:8100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/wda/, '')
      },
      // iOS MJPEG 流代理
      '/mjpeg': {
        target: 'http://localhost:9100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/mjpeg/, '')
      }
    }
  }
})
