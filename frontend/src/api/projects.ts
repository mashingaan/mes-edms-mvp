import apiClient from './client'
import { Project, ProjectCreate, ProjectUpdate, ProjectSection } from '../types/project'

export const getProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>('/api/projects')
  return response.data
}

export const getProject = async (id: string): Promise<Project> => {
  const response = await apiClient.get<Project>(`/api/projects/${id}`)
  return response.data
}

export const createProject = async (data: ProjectCreate): Promise<Project> => {
  const response = await apiClient.post<Project>('/api/projects', data)
  return response.data
}

export const updateProject = async (id: string, data: ProjectUpdate): Promise<Project> => {
  const response = await apiClient.patch<Project>(`/api/projects/${id}`, data)
  return response.data
}

export const deleteProject = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/projects/${id}`)
}

export const createSection = async (projectId: string, code: string): Promise<ProjectSection> => {
  const response = await apiClient.post<ProjectSection>(`/api/projects/${projectId}/sections`, { code })
  return response.data
}

export const getSections = async (projectId: string): Promise<ProjectSection[]> => {
  const response = await apiClient.get<ProjectSection[]>(`/api/projects/${projectId}/sections`)
  return response.data
}

