export type UserRole = 'admin' | 'responsible' | 'viewer'

export interface User {
  id: string
  full_name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface UserSummary {
  id: string
  full_name: string
  email: string
  role: UserRole
}

export interface UserCreate {
  full_name: string
  email: string
  password: string
  role: UserRole
}

export interface UserUpdate {
  full_name?: string
  email?: string
  role?: UserRole
  is_active?: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

