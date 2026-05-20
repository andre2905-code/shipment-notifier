import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import Layout from './layouts/Layout'
import { Toaster } from 'sonner'

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <App resource="/" /> },
      { path: '/blocos', element: <App resource="blocos" /> },
      { path: '/notificacoes', element: <App resource="notificacoes" /> },
    ]
  }
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Toaster position='top-center' />
    <RouterProvider router={router} />
  </StrictMode>,
)
