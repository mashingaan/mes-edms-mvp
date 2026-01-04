import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Navigate } from 'react-router-dom'
import { getAuditLogs } from '../api/audit'
import { usePermissions } from '../hooks/usePermissions'
import { formatDateTime } from '../utils/formatters'
import { ChevronDown, ChevronRight } from 'lucide-react'

export function AuditLogPage() {
  const { isAdmin } = usePermissions()
  const [page, setPage] = useState(1)
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['auditLogs', page],
    queryFn: () => getAuditLogs({ page, per_page: 50 }),
  })

  const toggleExpand = (id: number) => {
    const newSet = new Set(expandedIds)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setExpandedIds(newSet)
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
      <h1 className="text-2xl font-bold text-gray-900">Журнал аудита</h1>

      <div className="card overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="w-8"></th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Время</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действие</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs.map((log) => (
              <>
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-2">
                    <button
                      onClick={() => toggleExpand(log.id)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      {expandedIds.has(log.id) ? (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-500" />
                      )}
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDateTime(log.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {log.user?.full_name || 'Система'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-mono bg-gray-100 rounded">
                      {log.action_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.ip_address || '-'}
                  </td>
                </tr>
                {expandedIds.has(log.id) && (
                  <tr key={`${log.id}-details`}>
                    <td colSpan={5} className="px-6 py-4 bg-gray-50">
                      <pre className="text-xs text-gray-600 overflow-x-auto">
                        {JSON.stringify(log.payload, null, 2)}
                      </pre>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-center gap-2">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="btn-secondary"
        >
          Назад
        </button>
        <span className="px-4 py-2 text-gray-600">Страница {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={logs.length < 50}
          className="btn-secondary"
        >
          Вперёд
        </button>
      </div>
    </div>
  )
}

