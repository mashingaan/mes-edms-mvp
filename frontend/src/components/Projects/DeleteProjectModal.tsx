import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { deleteProject } from '../../api/projects'
import { Project } from '../../types/project'

interface DeleteProjectModalProps {
  isOpen: boolean
  onClose: () => void
  project: Project | null
  onSuccess: () => void
}

export function DeleteProjectModal({ isOpen, onClose, project, onSuccess }: DeleteProjectModalProps) {
  const [error, setError] = useState<string | null>(null)
  const [confirmCascade, setConfirmCascade] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => deleteProject(project!.id),
    onSuccess: () => {
      onSuccess()
    },
    onError: (err: any) => {
      const message = err.response?.data?.detail || 'Ошибка при удалении проекта'
      setError(message)
    },
  })

  const handleClose = () => {
    if (deleteMutation.isPending) return
    setError(null)
    setConfirmCascade(false)
    onClose()
  }

  if (!project) return null

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Удалить проект">
      <div className="space-y-4">
        <p className="text-gray-600">Удалить проект "{project.name}"?</p>

        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg space-y-2">
          <p className="text-sm text-yellow-800">
            Удалятся все связанные данные проекта (разделы/документы/изделия).
          </p>
          <ul className="list-disc pl-5 text-sm text-yellow-800 space-y-1">
            <li>Все разделы проекта</li>
            <li>Все items проекта</li>
            <li>Все технологические документы разделов</li>
            <li>Все документы items</li>
            <li>История прогресса</li>
          </ul>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={confirmCascade}
            onChange={(e) => setConfirmCascade(e.target.checked)}
          />
          Подтверждаю удаление всех связанных данных
        </label>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={deleteMutation.isPending}
          >
            Отмена
          </button>
          <button
            onClick={() => {
              setError(null)
              deleteMutation.mutate()
            }}
            disabled={deleteMutation.isPending || !confirmCascade}
            className="px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {deleteMutation.isPending ? 'Удаление...' : 'Удалить'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
