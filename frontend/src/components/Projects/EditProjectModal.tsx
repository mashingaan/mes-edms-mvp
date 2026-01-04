import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { updateProject } from '../../api/projects'
import { Project, ProjectStatus } from '../../types/project'

interface EditProjectModalProps {
  isOpen: boolean
  onClose: () => void
  project: Project | null
  onSuccess: () => void
}

const statusOptions: { value: ProjectStatus; label: string }[] = [
  { value: 'active', label: 'Активный' },
  { value: 'on_hold', label: 'На паузе' },
  { value: 'archived', label: 'В архиве' },
]

export function EditProjectModal({ isOpen, onClose, project, onSuccess }: EditProjectModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<ProjectStatus>('active')

  useEffect(() => {
    if (project) {
      setName(project.name)
      setDescription(project.description || '')
      setStatus(project.status)
    }
  }, [project])

  const mutation = useMutation({
    mutationFn: () => {
      if (!project) throw new Error('No project')
      return updateProject(project.id, { name, description: description || undefined, status })
    },
    onSuccess: () => {
      onSuccess()
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    mutation.mutate()
  }

  if (!project) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Редактировать проект">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Название проекта *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input"
            maxLength={255}
            required
          />
        </div>

        <div>
          <label className="label">Описание</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input min-h-[80px]"
          />
        </div>

        <div>
          <label className="label">Статус</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ProjectStatus)}
            className="input"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {mutation.isError && (
          <p className="text-sm text-red-600">Ошибка при сохранении проекта</p>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn-secondary">
            Отмена
          </button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending || !name.trim()}>
            {mutation.isPending ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

