import { fileURLToPath, URL } from 'node:url'
import process from 'node:process'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  // Only this opt-in preview is used for the temporary Instagram OAuth tunnel.
  preview: process.env.INSTAGRAM_PREVIEW_HOST ? {
    host: '127.0.0.1',
    port: 5176,
    strictPort: true,
    allowedHosts: [process.env.INSTAGRAM_PREVIEW_HOST],
    headers: { 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store' },
    proxy: { '/api/': { target: 'http://127.0.0.1:8002', changeOrigin: true } },
  } : {},
})
