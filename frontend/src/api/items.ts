import apiClient from './client'
import { Item, ItemCreate, ItemUpdate, ProgressUpdate, ProgressHistory } from '../types/item'

export interface ImportResult {
  created_count: number
  errors: Array<{ filename: string; error: string }>
}

export const getItems = async (projectId?: string, sectionId?: string): Promise<Item[]> => {
  const params: Record<string, string> = {}
  if (projectId) params.project_id = projectId
  if (sectionId) params.section_id = sectionId
  const response = await apiClient.get<Item[]>('/api/items', { params })
  return response.data
}

export const getItem = async (id: string): Promise<Item> => {
  const response = await apiClient.get<Item>(`/api/items/${id}`)
  return response.data
}

export const createItem = async (data: ItemCreate): Promise<Item> => {
  const response = await apiClient.post<Item>('/api/items', data)
  return response.data
}

export const updateItem = async (id: string, data: ItemUpdate): Promise<Item> => {
  const response = await apiClient.patch<Item>(`/api/items/${id}`, data)
  return response.data
}

export const deleteItem = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/items/${id}`)
}

export const updateProgress = async (id: string, data: ProgressUpdate): Promise<Item> => {
  const response = await apiClient.patch<Item>(`/api/items/${id}/progress`, data)
  return response.data
}

export const getProgressHistory = async (id: string): Promise<ProgressHistory[]> => {
  const response = await apiClient.get<ProgressHistory[]>(`/api/items/${id}/progress-history`)
  return response.data
}

export const importItems = async (
  projectId: string,
  files: File[],
  sectionId?: string,
  responsibleId?: string
): Promise<ImportResult> => {
  const formData = new FormData()
  formData.append('project_id', projectId)
  
  files.forEach((file) => {
    formData.append('files', file)
  })
  
  if (sectionId) {
    formData.append('section_id', sectionId)
  }
  
  if (responsibleId) {
    formData.append('responsible_id', responsibleId)
  }
  
  const response = await apiClient.post<ImportResult>('/api/items/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

