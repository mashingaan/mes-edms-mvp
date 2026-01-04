import { UserSummary } from './user'
import { DocumentSummary } from './document'
import { ProjectSection } from './project'

export type ItemStatus = 'draft' | 'in_progress' | 'completed' | 'cancelled'

export interface Item {
  id: string
  project_id: string
  section_id: string | null
  section: ProjectSection | null
  part_number: string
  name: string
  status: ItemStatus
  current_progress: number
  docs_completion_percent: number | null
  responsible: UserSummary | null
  documents: DocumentSummary[]
  created_at: string
  original_filename: string | null
}

export interface ItemSummary {
  id: string
  part_number: string
  name: string
  status: ItemStatus
  current_progress: number
  section_id: string | null
  original_filename: string | null
}

export interface FileImportPreview {
  filename: string
  parsed_section_code: string | null
  parsed_part_number: string | null
  parsed_name: string
}

export interface ItemCreate {
  project_id: string
  part_number: string
  name: string
  docs_completion_percent?: number
  responsible_id?: string
  status?: ItemStatus
}

export interface ItemUpdate {
  name?: string
  status?: ItemStatus
  docs_completion_percent?: number
  responsible_id?: string
  section_id?: string
}

export interface ProgressUpdate {
  new_progress: number
  comment?: string
}

export interface ProgressHistory {
  id: string
  item_id: string
  old_progress: number
  new_progress: number
  changed_by: UserSummary
  changed_at: string
  comment: string | null
}

