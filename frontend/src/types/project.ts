import { ItemSummary } from './item'

export type ProjectStatus = 'active' | 'archived' | 'on_hold'

export interface ProjectSection {
  id: string
  project_id: string
  code: string
  created_at: string
}

export interface Project {
  id: string
  name: string
  status: ProjectStatus
  description: string | null
  created_at: string
  items: ItemSummary[]
  sections: ProjectSection[]
}

export interface ProjectSummary {
  id: string
  name: string
  status: ProjectStatus
}

export interface ProjectCreate {
  name: string
  description?: string
  status?: ProjectStatus
}

export interface ProjectUpdate {
  name?: string
  description?: string
  status?: ProjectStatus
}

