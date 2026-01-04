import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Upload, Trash2, Edit2 } from 'lucide-react'
import { getProject, deleteProject } from '../api/projects'
import { getItems } from '../api/items'
import { ItemCard } from '../components/Items/ItemCard'
import { Modal } from '../components/Common/Modal'
import { SectionSelector } from '../components/Projects/SectionSelector'
import { ImportItemsModal } from '../components/Items/ImportItemsModal'
import { EditProjectModal } from '../components/Projects/EditProjectModal'
import { EditItemModal } from '../components/Items/EditItemModal'
import { usePermissions } from '../hooks/usePermissions'
import { Item } from '../types/item'

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { isAdmin } = usePermissions()
  const [showImportModal, setShowImportModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingItem, setEditingItem] = useState<Item | null>(null)
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null)

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id!),
    enabled: !!id,
  })

  // Fetch items filtered by section
  const { data: filteredItems = [] } = useQuery({
    queryKey: ['items', id, selectedSectionId],
    queryFn: () => {
      if (selectedSectionId === 'none') {
        // Special case: items without section - we need to filter client-side
        return getItems(id!, undefined)
      }
      return getItems(id!, selectedSectionId || undefined)
    },
    enabled: !!id,
    select: (items) => {
      if (selectedSectionId === 'none') {
        return items.filter((item) => !item.section_id)
      }
      return items
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteProject(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/projects')
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Проект не найден</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/projects" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
            {project.description && (
              <p className="text-gray-500">{project.description}</p>
            )}
          </div>
        </div>
        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowEditModal(true)}
              className="btn-secondary flex items-center gap-2"
            >
              <Edit2 className="h-4 w-4" />
              Редактировать
            </button>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="btn-secondary text-red-600 hover:bg-red-50 flex items-center gap-2"
              disabled={deleteMutation.isPending}
            >
              <Trash2 className="h-4 w-4" />
              {deleteMutation.isPending ? 'Удаление...' : 'Удалить проект'}
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Изделия ({filteredItems.length})
        </h2>
        {isAdmin && (
          <button onClick={() => setShowImportModal(true)} className="btn-primary flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Импортировать файлы
          </button>
        )}
      </div>

      <SectionSelector
        projectId={id!}
        selectedSectionId={selectedSectionId}
        onSectionChange={setSelectedSectionId}
      />

      {filteredItems.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Нет изделий</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((item) => (
            <ItemCard key={item.id} item={item} onEditClick={(item) => setEditingItem(item)} />
          ))}
        </div>
      )}

      <ImportItemsModal
        projectId={id!}
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['project', id] })
          queryClient.invalidateQueries({ queryKey: ['items', id] })
        }}
      />

      <EditProjectModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        project={project}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['project', id] })
          queryClient.invalidateQueries({ queryKey: ['projects'] })
        }}
      />

      <EditItemModal
        isOpen={!!editingItem}
        onClose={() => setEditingItem(null)}
        item={editingItem}
        projectId={id!}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['items', id] })
          queryClient.invalidateQueries({ queryKey: ['project', id] })
        }}
      />

      <Modal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} title="Удалить проект">
        <div className="space-y-4">
          <p className="text-gray-600">
            Вы уверены, что хотите удалить проект "{project.name}"? Это действие нельзя отменить.
          </p>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowDeleteModal(false)}
              className="btn-secondary"
            >
              Отмена
            </button>
            <button
              type="button"
              onClick={() => deleteMutation.mutate()}
              className="btn-primary bg-red-600 hover:bg-red-700"
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Удаление...' : 'Удалить'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

