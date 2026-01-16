export interface TechDocument {
  id: string
  section_id: string
  filename: string
  size_bytes: number
  version: number
  created_at: string
  created_by_user: {
    id: string
    full_name: string
  }
}

export interface TechDocumentVersion {
  id: string
  version: number
  filename: string
  created_at: string
  created_by_user: {
    id: string
    full_name: string
  }
}

export interface SheetPreview {
  name: string
  rows: string[][]
  total_rows: number
}

export interface TechDocumentPreview {
  filename: string
  sheets: SheetPreview[]
}
