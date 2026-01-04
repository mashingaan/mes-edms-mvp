import apiClient from './client'
import { AuditLog } from '../types/audit'

export interface AuditFilters {
  page?: number
  per_page?: number
  user_id?: string
  action_type?: string
  start_date?: string
  end_date?: string
}

export const getAuditLogs = async (filters: AuditFilters = {}): Promise<AuditLog[]> => {
  const response = await apiClient.get<AuditLog[]>('/api/audit', { params: filters })
  return response.data
}

