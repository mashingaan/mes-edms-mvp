import axios from 'axios'

// Динамическое определение API URL по текущему хосту
const getApiBaseUrl = (): string => {
  // Если задан явно через env - используем его
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  // Default: same-origin (nginx proxies /api)
  return window.location.origin
}

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
})

// Token management with localStorage persistence
const TOKEN_STORAGE_KEY = 'mes_access_token'

export const setAccessToken = (token: string | null) => {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }
}

export const getAccessToken = (): string | null => {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

// Request interceptor: Add Authorization header
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: Handle 401 (MVP: redirect to login, no refresh)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear token from localStorage and redirect to login (MVP simple auth)
      setAccessToken(null)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient

