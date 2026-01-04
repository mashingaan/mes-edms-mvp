import { useAuth } from './useAuth'
import { Item } from '../types/item'

export function usePermissions() {
  const { user } = useAuth()

  const isAdmin = user?.role === 'admin'
  const isViewer = user?.role === 'viewer'
  const isResponsible = user?.role === 'responsible'

  const canEditItem = (item: Item): boolean => {
    if (!user) return false
    if (isAdmin) return true
    if (isResponsible && item.responsible?.id === user.id) return true
    return false
  }

  const canUploadDocument = (item: Item): boolean => {
    return canEditItem(item)
  }

  const canDeleteDocument = (item: Item): boolean => {
    return canEditItem(item)
  }

  const canUpdateProgress = (item: Item): boolean => {
    return canEditItem(item)
  }

  const canManageUsers = (): boolean => {
    return isAdmin
  }

  const canViewAuditLog = (): boolean => {
    return isAdmin
  }

  const canCreateProject = (): boolean => {
    return isAdmin
  }

  const canDeleteProject = (): boolean => {
    return isAdmin
  }

  return {
    isAdmin,
    isViewer,
    isResponsible,
    canEditItem,
    canUploadDocument,
    canDeleteDocument,
    canUpdateProgress,
    canManageUsers,
    canViewAuditLog,
    canCreateProject,
    canDeleteProject,
  }
}

