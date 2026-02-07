import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// import './index.css'
// import './assets/css/style.css'
import App from './App'   // remove .tsx extension

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

