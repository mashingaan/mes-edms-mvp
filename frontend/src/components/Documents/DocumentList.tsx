import { useState } from 'react'
import { FileText, Download, Eye, Upload, Trash2 } from 'lucide-react'
import { Document } from '../../types/document'
import { formatFileSize } from '../../utils/formatters'
import { getDownloadUrl, getPreviewUrl } from '../../api/documents'
import { getAccessToken } from '../../api/client'
import { DocumentUploadModal } from './DocumentUploadModal'
import { RevisionHistory } from './RevisionHistory'
import { PDFViewer } from './PDFViewer'
import { DeleteDocumentModal } from './DeleteDocumentModal'
import { usePermissions } from '../../hooks/usePermissions'

interface DocumentListProps {
  documents: Document[]
  itemId: string
  canUpload: boolean
  canDelete: boolean
  showDeletedMode?: boolean
  onDocumentCreated?: () => void
  onDocumentDeleted?: () => void
}

export function DocumentList({ 
  documents, 
  itemId, 
  canUpload,
  canDelete,
  showDeletedMode = false,
  onDocumentCreated,
  onDocumentDeleted 
}: DocumentListProps) {
  const { isAdmin } = usePermissions()
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [showRevisions, setShowRevisions] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const handleDownload = (doc: Document) => {
    if (!doc.current_revision) return
    
    const url = getDownloadUrl(doc.id, doc.current_revision.id)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', '')
    
    // Add auth header via fetch
    fetch(url, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob)
        link.href = blobUrl
        link.click()
        URL.revokeObjectURL(blobUrl)
      })
  }

  const handlePreview = (doc: Document) => {
    if (!doc.current_revision) return
    const url = getPreviewUrl(doc.id, doc.current_revision.id)
    setPreviewUrl(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Документы</h3>
        {canUpload && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            Загрузить документ
          </button>
        )}
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          Документы отсутствуют
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <FileText className={`h-8 w-8 ${doc.is_deleted ? 'text-gray-400' : 'text-red-500'}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <p className={`font-medium ${doc.is_deleted ? 'text-gray-400' : 'text-gray-900'}`}>{doc.title}</p>
                    {showDeletedMode && doc.is_deleted && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded">
                        Удален
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    {doc.type && `${doc.type} • `}
                    Ревизия: {doc.current_revision?.revision_label || '-'}
                    {doc.current_revision && (
                      <> • {formatFileSize(doc.current_revision.file_size_bytes)}</>
                    )}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setSelectedDocument(doc)
                    setShowRevisions(true)
                  }}
                  className="text-xs text-primary-600 hover:text-primary-700"
                >
                  История ({doc.revisions?.length || 0})
                </button>
                
                {doc.current_revision && (
                  <>
                    <button
                      onClick={() => handlePreview(doc)}
                      className="p-2 hover:bg-gray-100 rounded-lg"
                      title="Просмотр"
                    >
                      <Eye className="h-4 w-4 text-gray-600" />
                    </button>
                    <button
                      onClick={() => handleDownload(doc)}
                      className="p-2 hover:bg-gray-100 rounded-lg"
                      title="Скачать"
                    >
                      <Download className="h-4 w-4 text-gray-600" />
                    </button>
                  </>
                )}

                {canDelete && !doc.is_deleted && (
                  <button
                    onClick={() => {
                      setDocumentToDelete(doc)
                      setShowDeleteModal(true)
                    }}
                    className="p-2 hover:bg-red-50 rounded-lg text-red-600"
                    title="Удалить"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
                
                {canUpload && !doc.is_deleted && (
                  <button
                    onClick={() => {
                      setSelectedDocument(doc)
                      setShowUploadModal(true)
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                    title="Новая ревизия"
                  >
                    <Upload className="h-4 w-4 text-gray-600" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <DocumentUploadModal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false)
          setSelectedDocument(null)
        }}
        itemId={itemId}
        document={selectedDocument}
        onSuccess={() => {
          setShowUploadModal(false)
          setSelectedDocument(null)
          onDocumentCreated?.()
        }}
      />

      {selectedDocument && (
        <RevisionHistory
          isOpen={showRevisions}
          onClose={() => {
            setShowRevisions(false)
            setSelectedDocument(null)
          }}
          document={selectedDocument}
        />
      )}

      <PDFViewer
        url={previewUrl}
        onClose={() => setPreviewUrl(null)}
      />

      <DeleteDocumentModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false)
          setDocumentToDelete(null)
        }}
        document={documentToDelete}
        isAdmin={isAdmin}
        onSuccess={() => {
          setShowDeleteModal(false)
          setDocumentToDelete(null)
          onDocumentDeleted?.()
        }}
      />
    </div>
  )
}

