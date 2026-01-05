import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const appTitle =
  import.meta.env.MODE === 'production'
    ? 'stock-analyzer'
    : '(dev) stock-analyzer'
document.title = appTitle

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
