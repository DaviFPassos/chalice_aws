import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Variáveis (arquivo .env.local ou ambiente):
//   API_PROXY_TARGET  desenvolvimento: URL da API sem o "/api/" final, ex.:
//                     https://abc123.execute-api.sa-east-1.amazonaws.com
//                     O Vite repassa /api/* para lá, sem precisar de CORS.
//   VITE_API_URL      build de produção: URL completa da API (com /api/)
//   VITE_BASE         caminho base do site (GitHub Pages: /chalice_aws/)
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    base: env.VITE_BASE || '/',
    server: {
      proxy: env.API_PROXY_TARGET
        ? { '/api': { target: env.API_PROXY_TARGET, changeOrigin: true, secure: true } }
        : undefined,
    },
    test: {
      environment: 'jsdom',
    },
  }
})
