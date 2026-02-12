import React, { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import axios from 'axios'

interface User {
  id: number
  email: string
  username?: string
  role: string
  is_active: boolean
  is_verified: boolean
}

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (email: string, password: string, username?: string) => Promise<void>
  refreshToken: () => Promise<void>
  isAuthenticated: boolean
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const API_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

  useEffect(() => {
    const initializeAuth = async () => {
      const accessToken = localStorage.getItem('accessToken')
      const refreshToken = localStorage.getItem('refreshToken')

      if (accessToken && refreshToken) {
        try {
          // Try to get user profile with current access token
          const response = await axios.get(`${API_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${accessToken}` }
          })
          setUser(response.data)
        } catch (error) {
          // If access token is expired, try to refresh
          try {
            await refreshToken()
          } catch (refreshError) {
            // If refresh fails, clear tokens
            localStorage.removeItem('accessToken')
            localStorage.removeItem('refreshToken')
          }
        }
      }
      setIsLoading(false)
    }

    initializeAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username: email, // Backend expects username field
        password
      })

      const { access_token, refresh_token } = response.data

      localStorage.setItem('accessToken', access_token)
      localStorage.setItem('refreshToken', refresh_token)

      // Get user profile
      const userResponse = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      })

      setUser(userResponse.data)
    } catch (error) {
      throw new Error('Login failed')
    }
  }

  const register = async (email: string, password: string, username?: string) => {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        email,
        password,
        username
      })

      setUser(response.data)
    } catch (error) {
      throw new Error('Registration failed')
    }
  }

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        await axios.post(`${API_URL}/auth/logout`, { refresh_token: refreshToken }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      setUser(null)
    }
  }



  const value: AuthContextType = {
    user,
    login,
    logout,
    register,
    refreshToken,
    isAuthenticated: !!user,
    isLoading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
