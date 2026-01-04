import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, UserX, UserCheck } from 'lucide-react'
import { getUsers, createUser, updateUser } from '../api/users'
import { Modal } from '../components/Common/Modal'
import { usePermissions } from '../hooks/usePermissions'
import { Navigate } from 'react-router-dom'
import { User, UserRole } from '../types/user'

const roleLabels: Record<UserRole, string> = {
  admin: 'Администратор',
  responsible: 'Ответственный',
  viewer: 'Просмотр',
}

export function UsersPage() {
  const queryClient = useQueryClient()
  const { isAdmin } = usePermissions()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [newUser, setNewUser] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'viewer' as UserRole,
  })

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const createMutation = useMutation({
    mutationFn: () => createUser(newUser),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowCreateModal(false)
      setNewUser({ full_name: '', email: '', password: '', role: 'viewer' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<User> }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setEditingUser(null)
    },
  })

  const toggleActive = (user: User) => {
    updateMutation.mutate({ id: user.id, data: { is_active: !user.is_active } })
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />
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
        <h1 className="text-2xl font-bold text-gray-900">Пользователи</h1>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Добавить пользователя
        </button>
      </div>

      <div className="card overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Имя</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Роль</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="font-medium text-gray-900">{user.full_name}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">{user.email}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-700">
                    {roleLabels[user.role]}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {user.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <button
                    onClick={() => setEditingUser(user)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                    title="Редактировать"
                  >
                    <Edit2 className="h-4 w-4 text-gray-600" />
                  </button>
                  <button
                    onClick={() => toggleActive(user)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                    title={user.is_active ? 'Деактивировать' : 'Активировать'}
                  >
                    {user.is_active ? (
                      <UserX className="h-4 w-4 text-red-600" />
                    ) : (
                      <UserCheck className="h-4 w-4 text-green-600" />
                    )}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Добавить пользователя">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            createMutation.mutate()
          }}
          className="space-y-4"
        >
          <div>
            <label className="label">Полное имя *</label>
            <input
              type="text"
              value={newUser.full_name}
              onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
              className="input"
              required
            />
          </div>
          <div>
            <label className="label">Email *</label>
            <input
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
              className="input"
              required
            />
          </div>
          <div>
            <label className="label">Пароль *</label>
            <input
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              className="input"
              required
              minLength={8}
            />
          </div>
          <div>
            <label className="label">Роль *</label>
            <select
              value={newUser.role}
              onChange={(e) => setNewUser({ ...newUser, role: e.target.value as UserRole })}
              className="input"
            >
              <option value="viewer">Просмотр</option>
              <option value="responsible">Ответственный</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">
              Отмена
            </button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal isOpen={!!editingUser} onClose={() => setEditingUser(null)} title="Редактировать пользователя">
        {editingUser && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              updateMutation.mutate({
                id: editingUser.id,
                data: {
                  full_name: editingUser.full_name,
                  role: editingUser.role,
                },
              })
            }}
            className="space-y-4"
          >
            <div>
              <label className="label">Полное имя *</label>
              <input
                type="text"
                value={editingUser.full_name}
                onChange={(e) => setEditingUser({ ...editingUser, full_name: e.target.value })}
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Роль *</label>
              <select
                value={editingUser.role}
                onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value as UserRole })}
                className="input"
              >
                <option value="viewer">Просмотр</option>
                <option value="responsible">Ответственный</option>
                <option value="admin">Администратор</option>
              </select>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setEditingUser(null)} className="btn-secondary">
                Отмена
              </button>
              <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}

