import { Link } from 'react-router-dom'
import { FileText, Edit2 } from 'lucide-react'
import { ProgressBar } from '../Common/ProgressBar'
import { Item } from '../../types/item'
import { usePermissions } from '../../hooks/usePermissions'

interface ItemCardProps {
  item: Item
  onEditClick?: (item: Item) => void
}

const statusLabels: Record<string, string> = {
  draft: 'Черновик',
  in_progress: 'В работе',
  completed: 'Завершено',
  cancelled: 'Отменено',
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
}

export function ItemCard({ item, onEditClick }: ItemCardProps) {
  const { isAdmin } = usePermissions()

  return (
    <Link
      to={`/items/${item.id}`}
      className="block p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow relative"
    >
      {isAdmin && onEditClick && (
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            onEditClick(item)
          }}
          className="absolute top-3 right-3 p-1.5 hover:bg-gray-100 rounded-lg transition-colors z-10"
          title="Редактировать"
        >
          <Edit2 className="h-4 w-4 text-gray-500" />
        </button>
      )}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <p className="text-sm font-mono text-gray-500">{item.part_number}</p>
            {item.section && (
              <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded">
                {item.section.code}
              </span>
            )}
          </div>
          <h4 className="font-medium text-gray-900">{item.name}</h4>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[item.status]} ${isAdmin && onEditClick ? 'mr-8' : ''}`}>
          {statusLabels[item.status]}
        </span>
      </div>
      
      <div className="space-y-2">
        <ProgressBar value={item.current_progress} size="sm" />
        
        {item.original_filename && (
          <p className="text-xs text-gray-400 flex items-center gap-1 truncate">
            <FileText className="h-3 w-3" />
            {item.original_filename}
          </p>
        )}
        
        {item.responsible && (
          <p className="text-xs text-gray-500">
            Ответственный: {item.responsible.full_name}
          </p>
        )}
      </div>
    </Link>
  )
}

