import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5000,
    allowedHosts: ["bnox.org"],
    proxy: {
      '/narrators': 'http://localhost:8000',
      '/videos': 'http://localhost:8000',
      '/project': 'http://localhost:8000',
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true
      },
      '/generate-tts': 'http://localhost:8000',
      '/generate-creative-script': 'http://localhost:8000',
      '/refine-script': 'http://localhost:8000',
      '/approve-creative-project': 'http://localhost:8000',
      '/generate-forge-video': 'http://localhost:8000',
      '/video-info': 'http://localhost:8000',
      '/download-social': 'http://localhost:8000',
      '/static': 'http://localhost:8000',

      '/download-file': 'http://localhost:8000'
    }
  }
})
