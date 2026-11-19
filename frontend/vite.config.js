import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Le front appelle "/api/..." ; en développement, Vite redirige vers le backend FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
});
