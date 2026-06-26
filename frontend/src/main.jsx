import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/tokens.css'   // design tokens — must load first
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
