import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

console.log('main.tsx loaded') 
console.log('Starting main.tsx')

try {
  console.log('About to import App')
  import('./App').then(module => {
    console.log('App imported successfully:', module)
  }).catch(err => {
    console.error('Failed to import App:', err)
  })
} catch (err) {
  console.error('Error in main.tsx:', err)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)