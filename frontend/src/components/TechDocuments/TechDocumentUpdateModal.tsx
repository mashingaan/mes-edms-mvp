import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { FileUpload } from '../Common/FileUpload'
import { updateTechDocument } from '../../api/tech_documents'
import { TechDocument } from '../../types/tech_document'

interface TechDocumentUpdateModalProps {
  isOpen: boolean
  onClose: () => void
  document: TechDocument | null
  onSuccess?: () => void
}

export function TechDocumentUpdateModal({
  isOpen,
  onClose,
  document,
  onSuccess,
}: TechDocumentUpdateModalProps) {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [updatedVersion, setUpdatedVersion] = useState<number | null>(null)

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!file || !document) throw new Error('No file selected')
      return updateTechDocument(document.id, file)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tech-documents', document?.section_id] })
      setUpdatedVersion(data.version)
      setFile(null)
      setError(null)
      onSuccess?.()
    },
    onError: (err: Error) => {
      setError(err.message || 'Ошибка при обновлении документа')
    },
  })

  const handleClose = () => {
    setFile(null)
    setError(null)
    setUpdatedVersion(null)
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!file) {
      setError('Выберите файл')
      return
    }

    updateMutation.mutate()
  }

  if (!document) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Загрузить новую версию документа ${document.filename}`}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Excel файл *</label>
          <FileUpload
            accept=".xlsx,.xlsm"
            maxSizeMB={100}
            onFileSelect={setFile}
            error={error && !file ? error : undefined}
          />
        </div>

        {error && file && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        {updatedVersion !== null && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-700">
              Новая версия: {updatedVersion}
            </p>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="btn-secondary"
            disabled={updateMutation.isPending}
          >
            Отмена
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={updateMutation.isPending || !file}
          >
            {updateMutation.isPending ? 'Обновление...' : 'Обновить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
