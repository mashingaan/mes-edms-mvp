import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, Download, Upload, Trash2, ArrowLeft } from 'lucide-react'
import { getTechDocuments, downloadTechDocument } from '../api/tech_documents'
import { getSectionById } from '../api/projects'
import { TechDocument } from '../types/tech_document'
import { formatDateTime, formatFileSize } from '../utils/formatters'
import { usePermissions } from '../hooks/usePermissions'
import { TechDocumentUploadModal } from '../components/TechDocuments/TechDocumentUploadModal'
import { TechDocumentPreviewModal } from '../components/TechDocuments/TechDocumentPreviewModal'
import { TechDocumentUpdateModal } from '../components/TechDocuments/TechDocumentUpdateModal'
import { DeleteTechDocumentModal } from '../components/TechDocuments/DeleteTechDocumentModal'
import { DeleteSectionModal } from '../components/Projects/DeleteSectionModal'
import { Project, ProjectSection } from '../types/project'

interface TechNavigationState {
  project?: Project
  section?: ProjectSection
}

export function TechSectionDocumentsPage() {
  const { sectionId } = useParams<{ sectionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { isAdmin } = usePermissions()
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [showUpdateModal, setShowUpdateModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showDeleteSectionModal, setShowDeleteSectionModal] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<TechDocument | null>(null)

  const navigationState = (location.state as TechNavigationState) || {}
  const hasNavigationState = Boolean(location.state)
  const project = navigationState.project
  const section = navigationState.section

  const { data: sectionById } = useQuery({
    queryKey: ['project-section', sectionId],
    queryFn: () => getSectionById(sectionId as string),
    enabled: !!sectionId && !hasNavigationState,
  })

  const sectionData = section || sectionById
  const projectId = project?.id || sectionData?.project_id

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['tech-documents', sectionId],
    queryFn: () => getTechDocuments(sectionId as string),
    enabled: !!sectionId,
  })

  const handleDownload = async (doc: TechDocument) => {
    const blob = await downloadTechDocument(doc.id)
    const url = URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    link.download = doc.filename
    link.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/tech" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </Link>
          <div>
            <div className="text-sm text-gray-500">
              Технологический
              {project?.name && ` > ${project.name}`}
              {sectionData?.code && ` > ${sectionData.code}`}
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              {sectionData?.code || 'Раздел'}
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && projectId && sectionData && (
            <button
              onClick={() => setShowDeleteSectionModal(true)}
              className="px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Удалить раздел
            </button>
          )}
          <button
            onClick={() => isAdmin && setShowUploadModal(true)}
            disabled={!isAdmin}
            className={`btn-primary flex items-center gap-2 ${!isAdmin ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Upload className="h-4 w-4" />
            Добавить документ
          </button>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Нет документов</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Файл
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Версия
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Размер
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Создан
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Автор
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{doc.filename}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{doc.version}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{formatFileSize(doc.size_bytes)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{formatDateTime(doc.created_at)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{doc.created_by_user?.full_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          setSelectedDocument(doc)
                          setShowPreviewModal(true)
                        }}
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
                      <button
                        onClick={() => {
                          setSelectedDocument(doc)
                          setShowUpdateModal(true)
                        }}
                        disabled={!isAdmin}
                        className={`p-2 rounded-lg ${isAdmin ? 'hover:bg-gray-100' : 'opacity-50 cursor-not-allowed'}`}
                        title="Обновить"
                      >
                        <Upload className="h-4 w-4 text-gray-600" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedDocument(doc)
                          setShowDeleteModal(true)
                        }}
                        disabled={!isAdmin}
                        className={`p-2 rounded-lg ${isAdmin ? 'hover:bg-red-50 text-red-600' : 'opacity-50 cursor-not-allowed text-red-600'}`}
                        title="Удалить"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sectionId && (
        <TechDocumentUploadModal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          sectionId={sectionId}
          onSuccess={() => {
            setShowUploadModal(false)
            queryClient.invalidateQueries({ queryKey: ['tech-documents', sectionId] })
          }}
        />
      )}

      <TechDocumentPreviewModal
        isOpen={showPreviewModal}
        onClose={() => {
          setShowPreviewModal(false)
          setSelectedDocument(null)
        }}
        document={selectedDocument}
      />

      <TechDocumentUpdateModal
        isOpen={showUpdateModal}
        onClose={() => {
          setShowUpdateModal(false)
          setSelectedDocument(null)
        }}
        document={selectedDocument}
        onSuccess={() => {
          if (sectionId) {
            queryClient.invalidateQueries({ queryKey: ['tech-documents', sectionId] })
          }
        }}
      />

      <DeleteTechDocumentModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false)
          setSelectedDocument(null)
        }}
        document={selectedDocument}
        onSuccess={() => {
          setShowDeleteModal(false)
          setSelectedDocument(null)
          if (sectionId) {
            queryClient.invalidateQueries({ queryKey: ['tech-documents', sectionId] })
          }
        }}
      />

      {projectId && (
        <DeleteSectionModal
          isOpen={showDeleteSectionModal}
          onClose={() => setShowDeleteSectionModal(false)}
          section={sectionData || null}
          projectId={projectId}
          onSuccess={() => {
            setShowDeleteSectionModal(false)
            queryClient.invalidateQueries({ queryKey: ['sections', projectId] })
            navigate(`/tech/projects/${projectId}/sections`)
          }}
        />
      )}
    </div>
  )
}
