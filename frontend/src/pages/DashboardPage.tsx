import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FolderOpen, Package, Bell, TrendingUp } from 'lucide-react'
import { getProjects } from '../api/projects'
import { ProgressBar } from '../components/Common/ProgressBar'
import { useNotifications } from '../hooks/useNotifications'

export function DashboardPage() {
  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  const { unreadCount } = useNotifications()

  const activeProjects = projects.filter((p) => p.status === 'active')
  const totalItems = projects.reduce((sum, p) => sum + (p.items?.length || 0), 0)
  const inProgressItems = projects.reduce(
    (sum, p) => sum + (p.items?.filter((i) => i.status === 'in_progress').length || 0),
    0
  )

  const calculateProjectProgress = (items: { current_progress: number }[]) => {
    if (!items || items.length === 0) return 0
    const total = items.reduce((sum, item) => sum + item.current_progress, 0)
    return Math.round(total / items.length)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Панель управления</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-primary-100 rounded-lg">
            <FolderOpen className="h-6 w-6 text-primary-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Активных проектов</p>
            <p className="text-2xl font-bold text-gray-900">{activeProjects.length}</p>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Package className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Всего изделий</p>
            <p className="text-2xl font-bold text-gray-900">{totalItems}</p>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg">
            <TrendingUp className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">В работе</p>
            <p className="text-2xl font-bold text-gray-900">{inProgressItems}</p>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="p-3 bg-orange-100 rounded-lg">
            <Bell className="h-6 w-6 text-orange-600" />
          </div>
          <div>
            <p className="text-sm text-gray-500">Непрочитанных</p>
            <p className="text-2xl font-bold text-gray-900">{unreadCount}</p>
          </div>
        </div>
      </div>

      {/* Projects List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Проекты</h2>
          <Link to="/projects" className="text-sm text-primary-600 hover:text-primary-700">
            Все проекты →
          </Link>
        </div>

        {activeProjects.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Нет активных проектов</p>
        ) : (
          <div className="space-y-4">
            {activeProjects.slice(0, 5).map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{project.name}</h3>
                  <span className="text-sm text-gray-500">
                    {project.items?.length || 0} изделий
                  </span>
                </div>
                <ProgressBar 
                  value={calculateProjectProgress(project.items || [])} 
                  size="sm" 
                />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

