import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import fs from 'fs'

// SSL証明書のパス（Docker環境用）
const certKeyPath = '/app/certs/key.pem'
const certPath = '/app/certs/cert.pem'

// 証明書が存在する場合のみHTTPSを有効化（Docker環境）
const httpsConfig = fs.existsSync(certKeyPath) && fs.existsSync(certPath)
  ? {
      key: fs.readFileSync(certKeyPath),
      cert: fs.readFileSync(certPath),
    }
  : undefined

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: httpsConfig,
  },
})
