import apiClient from './client'
import { Document, Revision } from '../types/document'

const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  return window.location.origin
}

export const getDocuments = async (itemId?: string, showDeleted?: boolean): Promise<Document[]> => {
  const params = { ...(itemId && { item_id: itemId }), ...(showDeleted && { show_deleted: showDeleted }) }
  const response = await apiClient.get<Document[]>('/api/documents', { params })
  return response.data
}

export const getDocument = async (id: string): Promise<Document> => {
  const response = await apiClient.get<Document>(`/api/documents/${id}`)
  return response.data
}

export const createDocument = async (
  itemId: string,
  title: string,
  type: string | undefined,
  file: File
): Promise<Document> => {
  const formData = new FormData()
  formData.append('item_id', itemId)
  formData.append('title', title)
  if (type) {
    formData.append('type', type)
  }
  formData.append('file', file)
  
  const response = await apiClient.post<Document>('/api/documents', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const uploadRevision = async (
  documentId: string,
  changeNote: string,
  file: File
): Promise<Revision> => {
  const formData = new FormData()
  formData.append('change_note', changeNote)
  formData.append('file', file)
  
  const response = await apiClient.post<Revision>(
    `/api/documents/${documentId}/revisions`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const deleteDocument = async (id: string, hard?: boolean): Promise<void> => {
  await apiClient.delete(`/api/documents/${id}${hard ? '?hard=true' : ''}`)
}

export const getDownloadUrl = (documentId: string, revisionId: string): string => {
  const baseUrl = getApiBaseUrl()
  return `${baseUrl}/api/documents/${documentId}/revisions/${revisionId}/download`
}

export const getPreviewUrl = (documentId: string, revisionId: string): string => {
  const baseUrl = getApiBaseUrl()
  return `${baseUrl}/api/documents/${documentId}/revisions/${revisionId}/preview`
}

