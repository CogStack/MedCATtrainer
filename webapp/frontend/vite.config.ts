import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      vue: 'vue/dist/vue.esm-bundler.js',
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    sourcemap: true,
    assetsDir: 'static'
  },
  server: {
    proxy: {
      '^/api/concepts/*': {
        target: 'http://localhost:8983/solr',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/\/api\/concepts/, '/')
      },
      '^/api/*': {
        target: 'http://localhost:8001'
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `
          @import "./src/styles/_variables.scss";
          @import "./src/styles/_common.scss";
          @import "./src/styles/_tabs.scss";
        `
      }
    }
  }
})
