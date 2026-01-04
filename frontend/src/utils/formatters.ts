import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'

export function formatDate(dateString: string): string {
  const date = parseISO(dateString)
  return format(date, 'd MMM yyyy', { locale: ru })
}

export function formatDateTime(dateString: string): string {
  const date = parseISO(dateString)
  return format(date, 'd MMM yyyy, HH:mm', { locale: ru })
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Б'
  
  const k = 1024
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function formatProgress(progress: number): string {
  return `${progress}%`
}

