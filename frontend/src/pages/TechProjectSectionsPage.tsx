import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Plus, Trash2 } from 'lucide-react'
import { getProject, getSections, createSection } from '../api/projects'
import { Modal } from '../components/Common/Modal'
import { DeleteProjectModal } from '../components/Projects/DeleteProjectModal'
import { usePermissions } from '../hooks/usePermissions'
import { ProjectSection } from '../types/project'

export function TechProjectSectionsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { isAdmin } = usePermissions()
  const [showModal, setShowModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [sectionCode, setSectionCode] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId as string),
    enabled: !!projectId,
  })

  const { data: sections = [], isLoading: sectionsLoading } = useQuery({
    queryKey: ['sections', projectId],
    queryFn: () => getSections(projectId as string),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: () => createSection(projectId as string, sectionCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sections', projectId] })
      setShowModal(false)
      setSectionCode('')
      setError(null)
    },
    onError: (err: any) => {
      const message = err.response?.data?.detail || 'Ошибка при создании раздела'
      setError(message)
    },
  })

  if (projectLoading || sectionsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Проект не найден</p>
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
              Технологический &gt; {project.name}
            </div>
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          </div>
        </div>
        {isAdmin && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDeleteModal(true)}
              className="px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Удалить проект
            </button>
            <button
              onClick={() => setShowModal(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Добавить раздел
            </button>
          </div>
        )}
      </div>

      {sections.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Нет разделов</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sections.map((section: ProjectSection) => (
            <button
              key={section.id}
              onClick={() =>
                navigate(`/tech/sections/${section.id}/documents`, {
                  state: { project, section },
                })
              }
              className="card hover:shadow-lg transition-shadow text-left"
            >
              <h3 className="font-semibold text-gray-900">{section.code}</h3>
            </button>
          ))}
        </div>
      )}

      <DeleteProjectModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        project={project}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['projects'] })
          navigate('/tech')
        }}
      />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Создать раздел">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            setError(null)
            createMutation.mutate()
          }}
          className="space-y-4"
        >
          <div>
            <label className="label">Код раздела *</label>
            <input
              type="text"
              value={sectionCode}
              onChange={(e) => setSectionCode(e.target.value)}
              className="input"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
