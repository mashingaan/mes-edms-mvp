import { UserSummary } from './user'

export interface AuditLog {
  id: number
  timestamp: string
  user: UserSummary | null
  action_type: string
  ip_address: string | null
  payload: Record<string, unknown>
}

