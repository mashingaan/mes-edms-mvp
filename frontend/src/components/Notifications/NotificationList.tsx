import { Notification } from '../../types/notification'
import { formatDateTime } from '../../utils/formatters'
import { clsx } from 'clsx'

interface NotificationListProps {
  notifications: Notification[]
  onMarkAsRead: (id: string) => void
}

export function NotificationList({ notifications, onMarkAsRead }: NotificationListProps) {
  if (notifications.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 text-sm">
        Нет уведомлений
      </div>
    )
  }

  return (
    <div className="max-h-80 overflow-y-auto">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={clsx(
            'p-3 border-b border-gray-100 last:border-0 cursor-pointer hover:bg-gray-50',
            !notification.read_at && 'bg-primary-50'
          )}
          onClick={() => {
            if (!notification.read_at) {
              onMarkAsRead(notification.id)
            }
          }}
        >
          <p className={clsx(
            'text-sm',
            notification.read_at ? 'text-gray-600' : 'text-gray-900 font-medium'
          )}>
            {notification.message}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {formatDateTime(notification.created_at)}
          </p>
        </div>
      ))}
    </div>
  )
}

