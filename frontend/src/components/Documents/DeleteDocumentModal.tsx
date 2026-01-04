import { useState } from 'react'
import { Modal } from '../Common/Modal'
import { Document } from '../../types/document'
import { deleteDocument } from '../../api/documents'

interface DeleteDocumentModalProps {
  isOpen: boolean
  onClose: () => void
  document: Document | null
  isAdmin: boolean
  onSuccess: () => void
}

export function DeleteDocumentModal({
  isOpen,
  onClose,
  document,
  isAdmin,
  onSuccess,
}: DeleteDocumentModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [hardDelete, setHardDelete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    if (!document) return

    setIsDeleting(true)
    setError(null)

    try {
      await deleteDocument(document.id, hardDelete)
      onSuccess()
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Ошибка при удалении документа'
      setError(message)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    setError(null)
    setHardDelete(false)
    onClose()
  }

  if (!document) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Удалить документ">
      <div className="space-y-4">
        <p className="text-gray-600">
          Удалить документ "{document.title}"? Действие можно отменить только администратором.
        </p>

        {isAdmin && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={hardDelete}
                onChange={(e) => setHardDelete(e.target.checked)}
                className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
              />
              <span className="text-sm font-medium text-red-700">
                Удалить безвозвратно (hard delete)
              </span>
            </label>
            {hardDelete && (
              <p className="mt-2 text-xs text-red-600">
                Внимание: документ и все его ревизии будут удалены навсегда без возможности восстановления!
              </p>
            )}
          </div>
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
            disabled={isDeleting}
            className="px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? 'Удаление...' : 'Удалить'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

