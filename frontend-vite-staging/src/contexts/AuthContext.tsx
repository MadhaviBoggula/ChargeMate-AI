import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { AUTH_TOKEN_KEY, authApi } from '../lib/api'
import type { LoginRequest, RegisterRequest, User } from '../types/api'

import { AuthContext } from './auth-context'
import type { AuthContextValue, AuthProviderProps } from './auth-context'

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const currentUser = await authApi.me()
    setUser(currentUser)
    return currentUser
  }, [])

  const login = useCallback(async (data: LoginRequest) => {
    const tokenResponse = await authApi.login(data)

    window.sessionStorage.setItem(
      AUTH_TOKEN_KEY,
      tokenResponse.access_token,
    )

    try {
      const currentUser = await authApi.me()
      setUser(currentUser)
      return currentUser
    } catch (error) {
      window.sessionStorage.removeItem(AUTH_TOKEN_KEY)
      setUser(null)
      throw error
    }
  }, [])

  const register = useCallback(async (data: RegisterRequest) => {
    await authApi.register(data)

    return login({
      email: data.email,
      password: data.password,
    })
  }, [login])

  const logout = useCallback(() => {
    window.sessionStorage.removeItem(AUTH_TOKEN_KEY)
    setUser(null)
  }, [])

  useEffect(() => {
    let active = true

    const restoreSession = async () => {
      if (!window.sessionStorage.getItem(AUTH_TOKEN_KEY)) {
        if (active) setLoading(false)
        return
      }

      try {
        const currentUser = await authApi.me()
        if (active) setUser(currentUser)
      } catch {
        window.sessionStorage.removeItem(AUTH_TOKEN_KEY)
        if (active) setUser(null)
      } finally {
        if (active) setLoading(false)
      }
    }

    void restoreSession()

    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, loading, login, register, logout, refreshUser],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
