import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// ── Token / session providers ─────────────────────────────────────────────────
// Stores register themselves here after they're created (see main.jsx).
// This pattern avoids circular imports between client.js and the stores.
let _getAccessToken = () => null
let _getRefreshToken = () => null
let _getSessionKey = () => null
let _setAccessToken = () => {}
let _logout = () => {}

export function registerTokenProviders({ getAccessToken, getRefreshToken, getSessionKey, setAccessToken, logout }) {
  _getAccessToken = getAccessToken
  _getRefreshToken = getRefreshToken
  _getSessionKey = getSessionKey
  _setAccessToken = setAccessToken
  _logout = logout
}

// ── Request interceptor ───────────────────────────────────────────────────────
client.interceptors.request.use((config) => {
  const token = _getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`

  const sessionKey = _getSessionKey()
  if (sessionKey) config.headers['X-Session-Key'] = sessionKey

  return config
})

// ── Response interceptor — silent JWT refresh on 401 ─────────────────────────
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)))
  failedQueue = []
}

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`
          return client(original)
        })
      }

      original._retry = true
      isRefreshing = true

      try {
        const refreshToken = _getRefreshToken()
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post('/api/auth/refresh', null, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        })

        const newToken = data.data.access_token
        _setAccessToken(newToken)
        processQueue(null, newToken)
        original.headers.Authorization = `Bearer ${newToken}`
        return client(original)
      } catch (err) {
        processQueue(err, null)
        _logout()
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default client
