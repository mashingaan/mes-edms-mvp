export interface Notification {
  id: string
  message: string
  read_at: string | null
  created_at: string
  event_payload: Record<string, unknown> | null
}

