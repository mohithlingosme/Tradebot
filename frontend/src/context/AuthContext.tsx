import { createContext, useContext, useMemo, useState } from 'react'
import { loginRequest, registerRequest } from '../services/auth'

interface AuthContextValue {
  token: string | null
  username: string | null
  isAuthenticated: boolean
  login: (payload: { username: string; password: string }) => Promise<void>
  register: (payload: { username: string; email: string; password: string }) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [username, setUsername] = useState<string | null>(() => localStorage.getItem('username'))

  const persistSession = (sessionToken: string, userName?: string) => {
    setToken(sessionToken)
    setUsername(userName ?? null)
    localStorage.setItem('access_token', sessionToken)
    if (userName) {
      localStorage.setItem('username', userName)
    }
  }

  const login = async ({ username: user, password }: { username: string; password: string }) => {
    const data = await loginRequest({ username: user, password })
    if (!data?.access_token) {
      throw new Error('Invalid response from server.')
    }
    persistSession(data.access_token, data.user?.username ?? user)
  }

  const register = async ({
    username: user,
    email,
    password,
  }: {
    username: string
    email: string
    password: string
  }) => {
    const data = await registerRequest({ username: user, email, password })
    if (!data?.access_token) {
      throw new Error('Invalid response from server.')
    }
    persistSession(data.access_token, data.user?.username ?? user)
  }

  const logout = () => {
    setToken(null)
    setUsername(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
  }

  const value = useMemo(
    () => ({
      token,
      username,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [token, username]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
