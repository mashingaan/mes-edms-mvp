import { FileText } from 'lucide-react'
import { ProgressBar } from '../Common/ProgressBar'
import { Item } from '../../types/item'

interface ItemDetailsProps {
  item: Item
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

export function ItemDetails({ item }: ItemDetailsProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-mono text-gray-500">{item.part_number}</p>
            {item.section && (
              <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded">
                {item.section.code}
              </span>
            )}
          </div>
          <h2 className="text-xl font-semibold text-gray-900">{item.name}</h2>
          {item.original_filename && (
            <p className="text-sm text-gray-400 flex items-center gap-1 mt-1">
              <FileText className="h-4 w-4" />
              {item.original_filename}
            </p>
          )}
        </div>
        <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusColors[item.status]}`}>
          {statusLabels[item.status]}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-500">Ответственный</p>
          <p className="font-medium">
            {item.responsible?.full_name || 'Не назначен'}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-500">% документации выпущено</p>
          <p className="font-medium">{item.docs_completion_percent ?? 0}%</p>
        </div>
      </div>

      <div>
        <p className="text-sm text-gray-500 mb-2">Общий прогресс</p>
        <ProgressBar value={item.current_progress} size="lg" />
      </div>
    </div>
  )
}

