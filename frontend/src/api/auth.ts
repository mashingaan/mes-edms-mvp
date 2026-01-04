import apiClient from './client'
import { LoginCredentials, TokenResponse, User } from '../types/user'

export const login = async (credentials: LoginCredentials): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/api/auth/login', credentials)
  return response.data
}

export const logout = async (): Promise<void> => {
  await apiClient.post('/api/auth/logout')
}

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get<User>('/api/auth/me')
  return response.data
}

