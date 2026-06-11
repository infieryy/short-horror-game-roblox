import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev, proxy API + WebSocket to the session manager so `npm run dev`
// works against a locally running backend.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8765',
      '/session': {
        target: 'ws://127.0.0.1:8765',
        ws: true,
      },
    },
  },
});
