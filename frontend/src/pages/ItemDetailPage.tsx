import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Edit2 } from 'lucide-react'
import { getItem, getProgressHistory } from '../api/items'
import { getDocuments } from '../api/documents'
import { ItemDetails } from '../components/Items/ItemDetails'
import { ProgressEditor } from '../components/Items/ProgressEditor'
import { EditItemModal } from '../components/Items/EditItemModal'
import { DocumentList } from '../components/Documents/DocumentList'
import { usePermissions } from '../hooks/usePermissions'
import { formatDateTime } from '../utils/formatters'
import { Item } from '../types/item'

export function ItemDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const { canUpdateProgress, canUploadDocument, isAdmin } = usePermissions()
  const [showProgressEditor, setShowProgressEditor] = useState(false)
  const [showDeleted, setShowDeleted] = useState(false)
  const [editingItem, setEditingItem] = useState<Item | null>(null)

  const { data: item, isLoading } = useQuery({
    queryKey: ['item', id],
    queryFn: () => getItem(id!),
    enabled: !!id,
  })

  const { data: progressHistory = [] } = useQuery({
    queryKey: ['progressHistory', id],
    queryFn: () => getProgressHistory(id!),
    enabled: !!id,
  })

  const { data: documents = [], refetch: refetchDocuments } = useQuery({
    queryKey: ['documents', id, showDeleted],
    queryFn: () => getDocuments(id, showDeleted),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Изделие не найдено</p>
      </div>
    )
  }

  const canEdit = canUpdateProgress(item)
  const canUpload = canUploadDocument(item)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/projects/${item.project_id}`} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{item.part_number}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <ItemDetails item={item} />

          <div className="flex items-center gap-2">
            {isAdmin && (
              <button
                onClick={() => setEditingItem(item)}
                className="btn-secondary flex items-center gap-2"
              >
                <Edit2 className="h-4 w-4" />
                Редактировать изделие
              </button>
            )}
            {canEdit && (
              <button
                onClick={() => setShowProgressEditor(true)}
                className="btn-primary flex items-center gap-2"
              >
                <Edit2 className="h-4 w-4" />
                Обновить прогресс
              </button>
            )}
          </div>

          <div className="card">
            {isAdmin && (
              <div className="flex items-center justify-end mb-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showDeleted}
                    onChange={(e) => setShowDeleted(e.target.checked)}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-600">Показать удаленные</span>
                </label>
              </div>
            )}
            <DocumentList
              documents={documents}
              itemId={item.id}
              canUpload={canUpload}
              canDelete={canUpload}
              showDeletedMode={showDeleted}
              onDocumentCreated={() => refetchDocuments()}
              onDocumentDeleted={() => refetchDocuments()}
            />
          </div>
        </div>

        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">История прогресса</h3>
            {progressHistory.length === 0 ? (
              <p className="text-gray-500 text-center py-4">Нет записей</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {progressHistory.map((entry) => (
                  <div key={entry.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">
                        {entry.old_progress}% → {entry.new_progress}%
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDateTime(entry.changed_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {entry.changed_by.full_name}
                    </p>
                    {entry.comment && (
                      <p className="text-sm text-gray-600 mt-1">{entry.comment}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <ProgressEditor
        isOpen={showProgressEditor}
        onClose={() => setShowProgressEditor(false)}
        itemId={item.id}
        currentProgress={item.current_progress}
        projectId={item.project_id}
      />

      <EditItemModal
        isOpen={!!editingItem}
        onClose={() => setEditingItem(null)}
        item={editingItem}
        projectId={item.project_id}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['item', id] })
          queryClient.invalidateQueries({ queryKey: ['items', item.project_id] })
          queryClient.invalidateQueries({ queryKey: ['project', item.project_id] })
        }}
      />
    </div>
  )
}

