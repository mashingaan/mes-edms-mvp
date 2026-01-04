import { Modal } from '../Common/Modal'
import { Document } from '../../types/document'
import { formatDateTime, formatFileSize } from '../../utils/formatters'
import { CheckCircle } from 'lucide-react'

interface RevisionHistoryProps {
  isOpen: boolean
  onClose: () => void
  document: Document
}

export function RevisionHistory({ isOpen, onClose, document }: RevisionHistoryProps) {
  const revisions = document.revisions || []

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`История ревизий: ${document.title}`}
      size="lg"
    >
      {revisions.length === 0 ? (
        <p className="text-gray-500 text-center py-4">Нет ревизий</p>
      ) : (
        <div className="space-y-3">
          {revisions.map((rev) => (
            <div
              key={rev.id}
              className={`p-4 border rounded-lg ${
                rev.is_current ? 'border-primary-300 bg-primary-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      Ревизия {rev.revision_label}
                    </span>
                    {rev.is_current && (
                      <span className="flex items-center gap-1 text-xs text-primary-600">
                        <CheckCircle className="h-3 w-3" />
                        Текущая
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {rev.original_filename} • {formatFileSize(rev.file_size_bytes)}
                  </p>
                </div>
                <span className="text-sm text-gray-500">
                  {formatDateTime(rev.uploaded_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}

