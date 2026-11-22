import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// PREVIEW 2 publiee dans le sous-dossier /preview2/ de la meme Pages (EXC-M10).
export default defineConfig({
  plugins: [react()],
  base: './',
  server: { host: true, port: 5175 },
  build: { outDir: 'dist', assetsDir: 'assets' },
})
