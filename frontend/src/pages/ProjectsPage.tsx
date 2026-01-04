import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FolderOpen, Edit2 } from 'lucide-react'
import { getProjects, createProject } from '../api/projects'
import { ProgressBar } from '../components/Common/ProgressBar'
import { Modal } from '../components/Common/Modal'
import { EditProjectModal } from '../components/Projects/EditProjectModal'
import { usePermissions } from '../hooks/usePermissions'
import { Project } from '../types/project'

const statusLabels: Record<string, string> = {
  active: 'Активный',
  archived: 'В архиве',
  on_hold: 'На паузе',
}

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  archived: 'bg-gray-100 text-gray-700',
  on_hold: 'bg-yellow-100 text-yellow-700',
}

export function ProjectsPage() {
  const queryClient = useQueryClient()
  const { isAdmin } = usePermissions()
  const [showModal, setShowModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')
  const [editingProject, setEditingProject] = useState<Project | null>(null)

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  const createMutation = useMutation({
    mutationFn: () => createProject({ name: newProjectName, description: newProjectDescription }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setShowModal(false)
      setNewProjectName('')
      setNewProjectDescription('')
    },
  })

  const calculateProgress = (items: { current_progress: number }[]) => {
    if (!items || items.length === 0) return 0
    const total = items.reduce((sum, item) => sum + item.current_progress, 0)
    return Math.round(total / items.length)
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
        <h1 className="text-2xl font-bold text-gray-900">Проекты</h1>
        {isAdmin && (
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Создать проект
          </button>
        )}
      </div>

      {projects.length === 0 ? (
        <div className="card text-center py-12">
          <FolderOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Нет проектов</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="card hover:shadow-lg transition-shadow relative"
            >
              {isAdmin && (
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    setEditingProject(project)
                  }}
                  className="absolute top-3 right-3 p-1.5 hover:bg-gray-100 rounded-lg transition-colors z-10"
                  title="Редактировать"
                >
                  <Edit2 className="h-4 w-4 text-gray-500" />
                </button>
              )}
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-gray-900 pr-8">{project.name}</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[project.status]} ${isAdmin ? 'mr-8' : ''}`}>
                  {statusLabels[project.status]}
                </span>
              </div>
              
              {project.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.description}</p>
              )}
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Изделий: {project.items?.length || 0}</span>
                </div>
                <ProgressBar value={calculateProgress(project.items || [])} size="sm" />
              </div>
            </Link>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Создать проект">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            createMutation.mutate()
          }}
          className="space-y-4"
        >
          <div>
            <label className="label">Название проекта *</label>
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              className="input"
              required
            />
          </div>
          
          <div>
            <label className="label">Описание</label>
            <textarea
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
              className="input min-h-[80px]"
            />
          </div>

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

      <EditProjectModal
        isOpen={!!editingProject}
        onClose={() => setEditingProject(null)}
        project={editingProject}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['projects'] })
        }}
      />
    </div>
  )
}

