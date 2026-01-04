import { useCallback, useState } from 'react'
import { Upload, X, FileText } from 'lucide-react'
import { clsx } from 'clsx'

interface FileUploadProps {
  accept?: string
  maxSizeMB?: number
  onFileSelect: (file: File) => void
  error?: string
}

export function FileUpload({ 
  accept = '.pdf', 
  maxSizeMB = 100, 
  onFileSelect,
  error 
}: FileUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)

  const validateFile = useCallback((file: File): boolean => {
    // Check extension
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (accept && !accept.includes(`.${ext}`)) {
      setValidationError(`Разрешены только файлы: ${accept}`)
      return false
    }
    
    // Check size
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    if (file.size > maxSizeBytes) {
      setValidationError(`Максимальный размер файла: ${maxSizeMB} МБ`)
      return false
    }
    
    setValidationError(null)
    return true
  }, [accept, maxSizeMB])

  const handleFileChange = useCallback((file: File | null) => {
    if (file && validateFile(file)) {
      setSelectedFile(file)
      onFileSelect(file)
    }
  }, [validateFile, onFileSelect])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFileChange(file)
  }, [handleFileChange])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    handleFileChange(file)
  }, [handleFileChange])

  const clearFile = () => {
    setSelectedFile(null)
    setValidationError(null)
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
          dragOver ? 'border-primary-500 bg-primary-50' : 'border-gray-300',
          (error || validationError) && 'border-red-300 bg-red-50'
        )}
      >
        {selectedFile ? (
          <div className="flex items-center justify-center gap-3">
            <FileText className="h-8 w-8 text-primary-600" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} МБ
              </p>
            </div>
            <button
              type="button"
              onClick={clearFile}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              Перетащите файл сюда или{' '}
              <label className="text-primary-600 hover:text-primary-700 cursor-pointer">
                выберите
                <input
                  type="file"
                  accept={accept}
                  onChange={handleInputChange}
                  className="hidden"
                />
              </label>
            </p>
            <p className="mt-1 text-xs text-gray-500">
              PDF до {maxSizeMB} МБ
            </p>
          </>
        )}
      </div>
      
      {(error || validationError) && (
        <p className="text-sm text-red-600">{error || validationError}</p>
      )}
    </div>
  )
}

