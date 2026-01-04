import apiClient from './client'
import { User, UserCreate, UserUpdate } from '../types/user'

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/api/users')
  return response.data
}

export const getUser = async (id: string): Promise<User> => {
  const response = await apiClient.get<User>(`/api/users/${id}`)
  return response.data
}

export const createUser = async (data: UserCreate): Promise<User> => {
  const response = await apiClient.post<User>('/api/users', data)
  return response.data
}

export const updateUser = async (id: string, data: UserUpdate): Promise<User> => {
  const response = await apiClient.patch<User>(`/api/users/${id}`, data)
  return response.data
}

export const deleteUser = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/users/${id}`)
}

