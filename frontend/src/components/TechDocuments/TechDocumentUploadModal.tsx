import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { FileUpload } from '../Common/FileUpload'
import { uploadTechDocument } from '../../api/tech_documents'

interface TechDocumentUploadModalProps {
  isOpen: boolean
  onClose: () => void
  sectionId: string
  onSuccess?: () => void
}

export function TechDocumentUploadModal({
  isOpen,
  onClose,
  sectionId,
  onSuccess,
}: TechDocumentUploadModalProps) {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected')
      return uploadTechDocument(sectionId, file)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tech-documents', sectionId] })
      setFile(null)
      setError(null)
      onSuccess?.()
    },
    onError: (err: Error) => {
      setError(err.message || 'Ошибка при загрузке документа')
    },
  })

  const handleClose = () => {
    setFile(null)
    setError(null)
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!file) {
      setError('Выберите файл')
      return
    }

    uploadMutation.mutate()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Загрузить документ">
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

        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="btn-secondary"
            disabled={uploadMutation.isPending}
          >
            Отмена
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={uploadMutation.isPending || !file}
          >
            {uploadMutation.isPending ? 'Загрузка...' : 'Загрузить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
