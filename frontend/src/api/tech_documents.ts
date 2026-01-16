import apiClient from './client'
import { TechDocument, TechDocumentPreview, TechDocumentVersion } from '../types/tech_document'

export const getTechDocuments = async (sectionId: string): Promise<TechDocument[]> => {
  const response = await apiClient.get<TechDocument[]>(`/api/tech/sections/${sectionId}/documents`)
  return response.data
}

export const uploadTechDocument = async (sectionId: string, file: File): Promise<TechDocument> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<TechDocument>(
    `/api/tech/sections/${sectionId}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const downloadTechDocument = async (documentId: string): Promise<Blob> => {
  const response = await apiClient.get(`/api/tech/documents/${documentId}/download`, {
    responseType: 'blob',
  })
  return response.data
}

export const previewTechDocument = async (documentId: string): Promise<TechDocumentPreview> => {
  const response = await apiClient.get<TechDocumentPreview>(`/api/tech/documents/${documentId}/preview`)
  return response.data
}

export const updateTechDocument = async (documentId: string, file: File): Promise<TechDocument> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.put<TechDocument>(
    `/api/tech/documents/${documentId}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export const deleteTechDocument = async (documentId: string): Promise<void> => {
  await apiClient.delete(`/api/tech/documents/${documentId}`, {
    params: { mode: 'soft' },
  })
}

export const getTechDocumentVersions = async (documentId: string): Promise<TechDocumentVersion[]> => {
  const response = await apiClient.get<TechDocumentVersion[]>(
    `/api/tech/documents/${documentId}/versions`
  )
  return response.data
}
