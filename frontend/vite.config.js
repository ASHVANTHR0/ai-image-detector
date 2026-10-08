import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// Port 8000 is often taken (e.g. by Splunk), so the backend uses 8765. Override with AID_BACKEND_URL.
const backend = process.env.AID_BACKEND_URL ?? 'http://127.0.0.1:8765'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': backend,
    },
  },
})
