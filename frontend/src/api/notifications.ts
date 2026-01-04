import apiClient from './client'
import { Notification } from '../types/notification'

export const getNotifications = async (): Promise<Notification[]> => {
  const response = await apiClient.get<Notification[]>('/api/v1/notifications/my')
  return response.data
}

export const markAsRead = async (id: string): Promise<Notification> => {
  const response = await apiClient.patch<Notification>(`/api/v1/notifications/${id}/read`)
  return response.data
}

export const markAllAsRead = async (): Promise<void> => {
  await apiClient.patch('/api/v1/notifications/read-all')
}

