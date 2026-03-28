import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import { registerTokenProviders } from './api/client'
import { ToastProvider } from './components/ui/Toast'
import useAuthStore from './store/authStore'
import useCartStore from './store/cartStore'

// Register token providers once — avoids circular imports between client.js and stores
registerTokenProviders({
  getAccessToken: () => useAuthStore.getState().accessToken,
  getRefreshToken: () => useAuthStore.getState().refreshToken,
  getSessionKey: () => useCartStore.getState().sessionKey,
  setAccessToken: (token) => useAuthStore.getState().setAccessToken(token),
  logout: () => useAuthStore.getState().logout(),
})

// Init guest session key on startup
useCartStore.getState().initSessionKey()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 min
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ToastProvider>
          <App />
        </ToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
