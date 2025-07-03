import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Environment variables starting with VITE_ are automatically exposed
  // No additional configuration needed for VITE_API_BASE_URL
})
