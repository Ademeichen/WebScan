import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

<<<<<<< HEAD
// Vite 配置文件
=======
<<<<<<< HEAD
// Vite 配置文件
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  // 开发服务器配置
  server: {
    port: 5173,
    host: true,
    open: true,
    
    // API 代理配置
    proxy: {
      '/api': {
<<<<<<< HEAD
        target: 'http://127.0.0.1:8888',
=======
<<<<<<< HEAD
        target: 'http://127.0.0.1:8888',
=======
        target: 'http://127.0.0.1:3000',
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
        changeOrigin: true,
        secure: false
      }
    }
  },
  
  // 路径别名配置
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          axios: ['axios']
        }
      }
    }
  },
  
  // 预览服务器配置
  preview: {
    port: 4173,
    host: true,
    open: true
  }
})
<<<<<<< HEAD
=======
<<<<<<< HEAD
=======

>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
