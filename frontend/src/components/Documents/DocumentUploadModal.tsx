import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { FileUpload } from '../Common/FileUpload'
import { createDocument, uploadRevision } from '../../api/documents'
import { Document } from '../../types/document'

interface DocumentUploadModalProps {
  isOpen: boolean
  onClose: () => void
  itemId: string
  document?: Document | null
  onSuccess?: () => void
}

export function DocumentUploadModal({
  isOpen,
  onClose,
  itemId,
  document,
  onSuccess,
}: DocumentUploadModalProps) {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [type, setType] = useState('')
  const [changeNote, setChangeNote] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const isNewDocument = !document
  const currentRevision = document?.current_revision?.revision_label || '-'
  const requiresChangeNote = !isNewDocument && currentRevision !== '-'

  const createMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected')
      return createDocument(itemId, title, type || undefined, file)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['item', itemId] })
      queryClient.invalidateQueries({ queryKey: ['documents', itemId] })
      resetForm()
      onSuccess?.()
    },
    onError: (err: Error) => {
      setError(err.message || 'Ошибка при загрузке документа')
    },
  })

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file || !document) throw new Error('No file selected')
      return uploadRevision(document.id, changeNote, file)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['item', itemId] })
      queryClient.invalidateQueries({ queryKey: ['documents', itemId] })
      queryClient.invalidateQueries({ queryKey: ['document', document?.id] })
      resetForm()
      onSuccess?.()
    },
    onError: (err: Error) => {
      setError(err.message || 'Ошибка при загрузке ревизии')
    },
  })

  const resetForm = () => {
    setTitle('')
    setType('')
    setChangeNote('')
    setFile(null)
    setError(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!file) {
      setError('Выберите файл')
      return
    }

    if (isNewDocument) {
      if (!title.trim()) {
        setError('Введите название документа')
        return
      }
      createMutation.mutate()
    } else {
      if (requiresChangeNote && !changeNote.trim()) {
        setError('Введите примечание об изменениях')
        return
      }
      uploadMutation.mutate()
    }
  }

  const isLoading = createMutation.isPending || uploadMutation.isPending

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isNewDocument ? 'Загрузить документ' : `Новая ревизия: ${document?.title}`}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {isNewDocument && (
          <>
            <div>
              <label className="label">Название документа *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="input"
                placeholder="Например: Сборочный чертеж"
              />
            </div>
            
            <div>
              <label className="label">Тип документа</label>
              <input
                type="text"
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="input"
                placeholder="Например: Чертеж, Спецификация"
              />
            </div>
          </>
        )}

        {!isNewDocument && (
          <div>
            <label className="label">
              Примечание об изменениях {requiresChangeNote && '*'}
            </label>
            <textarea
              value={changeNote}
              onChange={(e) => setChangeNote(e.target.value)}
              className="input min-h-[80px]"
              placeholder="Опишите внесённые изменения"
            />
            {!requiresChangeNote && (
              <p className="text-xs text-gray-500 mt-1">
                Для первой ревизии примечание необязательно
              </p>
            )}
          </div>
        )}

        <div>
          <label className="label">PDF файл *</label>
          <FileUpload
            accept=".pdf"
            maxSizeMB={100}
            onFileSelect={setFile}
            error={error && !file ? error : undefined}
          />
        </div>

        {error && file && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary"
            disabled={isLoading}
          >
            Отмена
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading || !file}
          >
            {isLoading ? 'Загрузка...' : 'Загрузить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

