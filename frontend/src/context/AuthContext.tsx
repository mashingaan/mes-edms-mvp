import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, LoginCredentials } from '../types/user'
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth'
import { setAccessToken, getAccessToken } from '../api/client'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Restore session from localStorage on mount
    const restoreSession = async () => {
      const token = getAccessToken()
      if (token) {
        try {
          // Token exists in localStorage, hydrate user data
          const userData = await getMe()
          setUser(userData)
        } catch {
          // Token is invalid or expired, clear it from storage
          setAccessToken(null)
          setUser(null)
        }
      }
      setIsLoading(false)
    }
    
    restoreSession()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    const response = await apiLogin(credentials)
    setAccessToken(response.access_token)
    setUser(response.user)
  }

  const logout = async () => {
    try {
      await apiLogout()
    } catch {
      // Ignore logout errors
    }
    setAccessToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

