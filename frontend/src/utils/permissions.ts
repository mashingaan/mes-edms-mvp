import { User } from '../types/user'
import { Item } from '../types/item'

export const canEditItem = (user: User, item: Item): boolean => {
  if (user.role === 'admin') return true
  if (user.role === 'responsible' && item.responsible?.id === user.id) return true
  return false
}

export const canUploadDocument = (user: User, item: Item): boolean => {
  return canEditItem(user, item)
}

export const isAdmin = (user: User): boolean => user.role === 'admin'
export const isViewer = (user: User): boolean => user.role === 'viewer'
export const isResponsible = (user: User): boolean => user.role === 'responsible'

