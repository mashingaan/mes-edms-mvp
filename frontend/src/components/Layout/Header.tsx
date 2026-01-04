import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LogOut, User, Users, FileText } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import { usePermissions } from '../../hooks/usePermissions'
import { NotificationBell } from '../Notifications/NotificationBell'

export function Header() {
  const { user, logout } = useAuth()
  const { isAdmin } = usePermissions()
  const [showMenu, setShowMenu] = useState(false)

  const handleLogout = async () => {
    await logout()
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <Link 
          to="/projects" 
          className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          Проекты
        </Link>
        {isAdmin && (
          <>
            <Link 
              to="/users" 
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-2"
            >
              <Users className="h-4 w-4" />
              Пользователи
            </Link>
            <Link 
              to="/audit" 
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-2"
            >
              <FileText className="h-4 w-4" />
              Журнал аудита
            </Link>
          </>
        )}
      </div>
      
      <div className="flex items-center gap-4">
        <NotificationBell />
        
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100"
          >
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-primary-600" />
            </div>
            <span className="text-sm font-medium text-gray-700">
              {user?.full_name}
            </span>
          </button>
          
          {showMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
              <div className="px-4 py-2 border-b border-gray-100">
                <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
                <p className="text-xs text-primary-600 mt-1 capitalize">{user?.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <LogOut className="h-4 w-4" />
                Выйти
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

