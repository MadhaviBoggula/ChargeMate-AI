import { createContext } from 'react'
import type { ReactNode } from 'react'
import type { LoginRequest, RegisterRequest, User } from '../types/api'

export interface AuthContextValue {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (data: LoginRequest) => Promise<User>
  register: (data: RegisterRequest) => Promise<User>
  logout: () => void
  refreshUser: () => Promise<User>
}

export interface AuthProviderProps {
  children: ReactNode
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
)
