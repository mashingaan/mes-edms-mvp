import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { updateItem } from '../../api/items'
import { getSections } from '../../api/projects'
import { getUsers } from '../../api/users'
import { Item, ItemStatus } from '../../types/item'

interface EditItemModalProps {
  isOpen: boolean
  onClose: () => void
  item: Item | null
  projectId: string
  onSuccess: () => void
}

const statusOptions: { value: ItemStatus; label: string }[] = [
  { value: 'draft', label: 'Черновик' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'completed', label: 'Завершено' },
  { value: 'cancelled', label: 'Отменено' },
]

export function EditItemModal({ isOpen, onClose, item, projectId, onSuccess }: EditItemModalProps) {
  const [name, setName] = useState('')
  const [status, setStatus] = useState<ItemStatus>('draft')
  const [sectionId, setSectionId] = useState<string | null>(null)
  const [responsibleId, setResponsibleId] = useState<string | null>(null)
  const [docsCompletionPercent, setDocsCompletionPercent] = useState<number>(0)

  const { data: sections = [] } = useQuery({
    queryKey: ['sections', projectId],
    queryFn: () => getSections(projectId),
    enabled: isOpen && !!projectId,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    enabled: isOpen,
  })

  useEffect(() => {
    if (item) {
      setName(item.name)
      setStatus(item.status)
      setSectionId(item.section_id)
      setResponsibleId(item.responsible?.id || null)
      setDocsCompletionPercent(item.docs_completion_percent || 0)
    }
  }, [item])

  const mutation = useMutation({
    mutationFn: () => {
      if (!item) throw new Error('No item')
      return updateItem(item.id, {
        name,
        status,
        section_id: sectionId || undefined,
        responsible_id: responsibleId || undefined,
        docs_completion_percent: docsCompletionPercent,
      })
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

  if (!item) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Редактировать изделие">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Название *</label>
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
          <label className="label">Статус</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ItemStatus)}
            className="input"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Раздел</label>
          <select
            value={sectionId || ''}
            onChange={(e) => setSectionId(e.target.value || null)}
            className="input"
          >
            <option value="">Без раздела</option>
            {sections.map((section) => (
              <option key={section.id} value={section.id}>
                {section.code}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Ответственный</label>
          <select
            value={responsibleId || ''}
            onChange={(e) => setResponsibleId(e.target.value || null)}
            className="input"
          >
            <option value="">Не назначен</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.full_name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="label">Готовность документации (%)</label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="0"
              max="100"
              value={docsCompletionPercent}
              onChange={(e) => setDocsCompletionPercent(Number(e.target.value))}
              className="flex-1"
            />
            <input
              type="number"
              min="0"
              max="100"
              value={docsCompletionPercent}
              onChange={(e) => setDocsCompletionPercent(Math.min(100, Math.max(0, Number(e.target.value))))}
              className="input w-20 text-center"
            />
          </div>
        </div>

        {mutation.isError && (
          <p className="text-sm text-red-600">Ошибка при сохранении изделия</p>
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

