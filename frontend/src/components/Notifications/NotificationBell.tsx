import { useState } from 'react'
import { Bell } from 'lucide-react'
import { useNotifications } from '../../hooks/useNotifications'
import { NotificationList } from './NotificationList'

export function NotificationBell() {
  const [showDropdown, setShowDropdown] = useState(false)
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 hover:bg-gray-100 rounded-lg"
      >
        <Bell className="h-5 w-5 text-gray-600" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setShowDropdown(false)} 
          />
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            <div className="p-3 border-b border-gray-100 flex items-center justify-between">
              <h4 className="font-medium text-gray-900">Уведомления</h4>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllAsRead()}
                  className="text-xs text-primary-600 hover:text-primary-700"
                >
                  Прочитать все
                </button>
              )}
            </div>
            
            <NotificationList
              notifications={notifications.slice(0, 5)}
              onMarkAsRead={markAsRead}
            />
            
            {notifications.length > 5 && (
              <div className="p-3 border-t border-gray-100 text-center">
                <span className="text-xs text-gray-500">
                  +{notifications.length - 5} уведомлений
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

