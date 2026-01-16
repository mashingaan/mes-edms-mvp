import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { deleteSection } from '../../api/projects'
import { getTechDocuments } from '../../api/tech_documents'
import { ProjectSection } from '../../types/project'

interface DeleteSectionModalProps {
  isOpen: boolean
  onClose: () => void
  section: ProjectSection | null
  projectId: string
  onSuccess: () => void
}

export function DeleteSectionModal({
  isOpen,
  onClose,
  section,
  projectId,
  onSuccess,
}: DeleteSectionModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmCascade, setConfirmCascade] = useState(false)

  const sectionId = section?.id

  const { data: documents = [] } = useQuery({
    queryKey: ['tech-documents', sectionId],
    queryFn: () => getTechDocuments(sectionId as string),
    enabled: isOpen && !!sectionId,
  })

  const hasDocuments = documents.length > 0

  const handleDelete = async () => {
    if (!section) return

    setIsDeleting(true)
    setError(null)

    try {
      await deleteSection(projectId, section.id)
      onSuccess()
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Ошибка при удалении раздела'
      setError(message)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    setError(null)
    setConfirmCascade(false)
    onClose()
  }

  if (!section) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Удалить раздел">
      <div className="space-y-4">
        <p className="text-gray-600">
          Удалить раздел "{section.code}"?
        </p>

        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg space-y-1">
          <p className="text-sm text-yellow-800">
            При удалении раздела будут удалены все технологические документы (CASCADE).
          </p>
          {hasDocuments && (
            <p className="text-sm text-yellow-800">
              Документов в разделе: {documents.length}
            </p>
          )}
        </div>

        {hasDocuments && (
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={confirmCascade}
              onChange={(e) => setConfirmCascade(e.target.checked)}
            />
            Подтверждаю удаление документов
          </label>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={isDeleting}
          >
            Отмена
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting || (hasDocuments && !confirmCascade)}
            className="px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? 'Удаление...' : 'Удалить'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

