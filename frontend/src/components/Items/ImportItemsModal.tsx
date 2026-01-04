import { useState, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import { Modal } from '../Common/Modal'
import { importItems } from '../../api/items'
import { getSections } from '../../api/projects'
import { getUsers } from '../../api/users'
import { ProjectSection } from '../../types/project'
import { User } from '../../types/user'

interface ImportItemsModalProps {
  projectId: string
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface FilePreview {
  file: File
  parsedSectionCode: string | null
  parsedPartNumber: string | null
  parsedName: string
}

function parseFilename(filename: string): {
  section_code: string | null
  part_number: string | null
  name: string
} {
  // Remove extension
  let nameWithoutExt = filename
  if (filename.toLowerCase().endsWith('.pdf')) {
    nameWithoutExt = filename.slice(0, -4)
  }

  let remaining = nameWithoutExt.trim()
  let sectionCode: string | null = null
  let partNumber: string | null = null

  // Try to detect section code
  const sectionMatch = remaining.match(/^([A-ZА-Я0-9]+\.[A-ZА-Я0-9]+)\./i)
  if (sectionMatch) {
    sectionCode = sectionMatch[1]
    remaining = remaining.slice(sectionMatch[0].length).trim()
  }

  // Try to extract part_number
  const partNumberMatch = remaining.match(/^(\d{2,3}\.\d{3}\.\d{3}\.\d{3})\s*(.*)$/)
  if (partNumberMatch) {
    partNumber = partNumberMatch[1]
    remaining = partNumberMatch[2].trim()
  } else {
    const numericMatch = remaining.match(/^(\d{1,3})\.\s*(.*)$/)
    if (numericMatch) {
      partNumber = numericMatch[1]
      remaining = numericMatch[2].trim()
    }
  }

  const name = remaining || nameWithoutExt

  return {
    section_code: sectionCode,
    part_number: partNumber,
    name: name,
  }
}

export function ImportItemsModal({
  projectId,
  isOpen,
  onClose,
  onSuccess,
}: ImportItemsModalProps) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFiles, setSelectedFiles] = useState<FilePreview[]>([])
  const [sectionId, setSectionId] = useState<string>('')
  const [responsibleId, setResponsibleId] = useState<string>('')
  const [importResult, setImportResult] = useState<{
    created_count: number
    errors: Array<{ filename: string; error: string }>
  } | null>(null)

  const { data: sections = [] } = useQuery({
    queryKey: ['sections', projectId],
    queryFn: () => getSections(projectId),
    enabled: isOpen && !!projectId,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    enabled: isOpen,
  })

  const importMutation = useMutation({
    mutationFn: () =>
      importItems(
        projectId,
        selectedFiles.map((f) => f.file),
        sectionId || undefined,
        responsibleId || undefined
      ),
    onSuccess: (result) => {
      setImportResult(result)
      if (result.created_count > 0) {
        queryClient.invalidateQueries({ queryKey: ['project', projectId] })
        queryClient.invalidateQueries({ queryKey: ['items'] })
        queryClient.invalidateQueries({ queryKey: ['sections', projectId] })
      }
    },
  })

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const previews: FilePreview[] = []
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        const parsed = parseFilename(file.name)
        previews.push({
          file,
          parsedSectionCode: parsed.section_code,
          parsedPartNumber: parsed.part_number,
          parsedName: parsed.name,
        })
      }
    }

    setSelectedFiles((prev) => [...prev, ...previews])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleClose = () => {
    setSelectedFiles([])
    setSectionId('')
    setResponsibleId('')
    setImportResult(null)
    onClose()
  }

  const handleSuccessClose = () => {
    onSuccess()
    handleClose()
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  // Show result screen after import
  if (importResult) {
    return (
      <Modal isOpen={isOpen} onClose={handleClose} title="Результат импорта" size="lg">
        <div className="space-y-4">
          {importResult.created_count > 0 && (
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <span className="text-green-800 font-medium">
                Успешно создано изделий: {importResult.created_count}
              </span>
            </div>
          )}

          {importResult.errors.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-red-600 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Ошибки ({importResult.errors.length})
              </h4>
              <div className="max-h-48 overflow-y-auto space-y-2">
                {importResult.errors.map((err, idx) => (
                  <div key={idx} className="p-3 bg-red-50 rounded-lg text-sm">
                    <span className="font-medium">{err.filename}:</span>{' '}
                    <span className="text-red-700">{err.error}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end pt-4">
            <button onClick={handleSuccessClose} className="btn-primary">
              Закрыть
            </button>
          </div>
        </div>
      </Modal>
    )
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Импортировать файлы" size="lg">
      <div className="space-y-4">
        {/* File Selection */}
        <div>
          <label className="label">PDF файлы</label>
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 transition-colors"
          >
            <Upload className="h-8 w-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-600">
              Нажмите для выбора или перетащите PDF файлы
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Только PDF файлы
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Selected Files Preview */}
        {selectedFiles.length > 0 && (
          <div>
            <label className="label">Выбранные файлы ({selectedFiles.length})</label>
            <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-2">
              {selectedFiles.map((fp, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-5 w-5 text-red-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{fp.file.name}</p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(fp.file.size)}
                        {fp.parsedSectionCode && (
                          <span className="ml-2 text-primary-600">
                            [{fp.parsedSectionCode}]
                          </span>
                        )}
                        {fp.parsedPartNumber && (
                          <span className="ml-1 text-green-600">
                            {fp.parsedPartNumber}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(idx)}
                    className="p-1 hover:bg-gray-200 rounded"
                  >
                    <X className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section Selector */}
        <div>
          <label className="label">Раздел (необязательно)</label>
          <select
            value={sectionId}
            onChange={(e) => setSectionId(e.target.value)}
            className="input"
          >
            <option value="">Авто-определение из имени файла</option>
            {sections.map((section: ProjectSection) => (
              <option key={section.id} value={section.id}>
                {section.code}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Если не выбрано, раздел будет определен из имени файла
          </p>
        </div>

        {/* Responsible Selector */}
        <div>
          <label className="label">Ответственный (необязательно)</label>
          <select
            value={responsibleId}
            onChange={(e) => setResponsibleId(e.target.value)}
            className="input"
          >
            <option value="">Не назначен</option>
            {users.map((user: User) => (
              <option key={user.id} value={user.id}>
                {user.full_name} ({user.role})
              </option>
            ))}
          </select>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={handleClose} className="btn-secondary">
            Отмена
          </button>
          <button
            onClick={() => importMutation.mutate()}
            disabled={selectedFiles.length === 0 || importMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            {importMutation.isPending
              ? 'Импорт...'
              : `Импортировать (${selectedFiles.length})`}
          </button>
        </div>
      </div>
    </Modal>
  )
}

