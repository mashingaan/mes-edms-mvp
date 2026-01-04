import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { updateProgress } from '../../api/items'

interface ProgressEditorProps {
  isOpen: boolean
  onClose: () => void
  itemId: string
  currentProgress: number
  projectId: string
}

export function ProgressEditor({ isOpen, onClose, itemId, currentProgress, projectId }: ProgressEditorProps) {
  const queryClient = useQueryClient()
  const [progress, setProgress] = useState(currentProgress)
  const [comment, setComment] = useState('')

  const mutation = useMutation({
    mutationFn: () => updateProgress(itemId, { new_progress: progress, comment: comment || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['item', itemId] })
      queryClient.invalidateQueries({ queryKey: ['progressHistory', itemId] })
      queryClient.invalidateQueries({ queryKey: ['items', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Обновить прогресс">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Прогресс (%)</label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="0"
              max="100"
              value={progress}
              onChange={(e) => setProgress(Number(e.target.value))}
              className="flex-1"
            />
            <input
              type="number"
              min="0"
              max="100"
              value={progress}
              onChange={(e) => setProgress(Number(e.target.value))}
              className="input w-20 text-center"
            />
          </div>
        </div>

        <div>
          <label className="label">Комментарий (необязательно)</label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="input min-h-[80px]"
            placeholder="Опишите выполненную работу"
          />
        </div>

        {mutation.isError && (
          <p className="text-sm text-red-600">Ошибка при обновлении прогресса</p>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn-secondary">
            Отмена
          </button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

