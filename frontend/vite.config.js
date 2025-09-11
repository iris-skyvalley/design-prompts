import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/generate-prompt': 'http://localhost:8000',
      '/surprise-me': 'http://localhost:8000',
    },
  },
  build: {
    sourcemap: false, // Disable source maps in production
    rollupOptions: {
      output: {
        manualChunks: undefined, // Disable chunk splitting for simpler builds
      },
    },
  },
});
