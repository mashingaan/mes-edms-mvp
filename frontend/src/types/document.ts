import { UserSummary } from './user'

export interface RevisionSummary {
  id: string
  revision_label: string
  original_filename: string
  file_size_bytes: number
  is_current: boolean
  uploaded_at: string
}

export interface Revision {
  id: string
  document_id: string
  revision_label: string
  original_filename: string
  file_size_bytes: number
  is_current: boolean
  change_note: string | null
  author: UserSummary
  uploaded_at: string
}

export interface DocumentSummary {
  id: string
  title: string
  type: string | null
  created_at: string
}

export interface Document {
  id: string
  item_id: string
  title: string
  type: string | null
  current_revision: RevisionSummary | null
  revisions: RevisionSummary[]
  created_at: string
  is_deleted?: boolean
  deleted_at?: string
  deleted_by?: string
}

export interface DocumentCreate {
  item_id: string
  title: string
  type?: string
}

export interface RevisionCreate {
  change_note: string
}

