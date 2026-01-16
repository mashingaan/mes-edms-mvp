import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Modal } from '../Common/Modal'
import { previewTechDocument, downloadTechDocument } from '../../api/tech_documents'
import { TechDocument } from '../../types/tech_document'

interface TechDocumentPreviewModalProps {
  isOpen: boolean
  onClose: () => void
  document: TechDocument | null
}

export function TechDocumentPreviewModal({
  isOpen,
  onClose,
  document: techDocument,
}: TechDocumentPreviewModalProps) {
  const documentId = techDocument?.id
  const [selectedSheetIndex, setSelectedSheetIndex] = useState(0)
  const [isFullView, setIsFullView] = useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['tech-document-preview', documentId],
    queryFn: () => previewTechDocument(documentId as string),
    enabled: isOpen && !!documentId,
  })

  const sheets = useMemo(() => data?.sheets || [], [data])
  const selectedSheet = useMemo(() => sheets[selectedSheetIndex], [sheets, selectedSheetIndex])

  useEffect(() => {
    if (isOpen) {
      setSelectedSheetIndex(0)
      setIsFullView(false)
    }
  }, [documentId, isOpen])

  useEffect(() => {
    if (selectedSheetIndex >= sheets.length) {
      setSelectedSheetIndex(0)
    }
  }, [selectedSheetIndex, sheets.length])

  const handleDownload = async () => {
    if (!techDocument) return
    const blob = await downloadTechDocument(techDocument.id)
    const url = URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    link.download = techDocument.filename
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!techDocument) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={techDocument.filename}
      size={isFullView ? 'full' : '4xl'}
    >
      <div className="space-y-4">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        )}

        {isError && (
          <div className="text-sm text-red-600">
            Не удалось получить превью
          </div>
        )}

        {!isLoading && !isError && sheets.length === 0 && (
          <div className="text-sm text-gray-500">
            Нет данных
          </div>
        )}

        {!isLoading && !isError && sheets.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                {sheets.length > 1 && (
                  <>
                    <select
                      value={selectedSheetIndex}
                      onChange={(e) => setSelectedSheetIndex(Number(e.target.value))}
                      className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
                    >
                      {sheets.map((sheet, index) => (
                        <option key={sheet.name} value={index}>
                          {sheet.name}
                        </option>
                      ))}
                    </select>
                    <div className="text-xs text-gray-500">
                      Лист {selectedSheetIndex + 1} из {sheets.length}
                    </div>
                  </>
                )}
              </div>

              <button
                type="button"
                onClick={() => setIsFullView((prev) => !prev)}
                className="px-3 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {isFullView ? 'Обычный вид' : 'Развернуть'}
              </button>
            </div>

            {selectedSheet && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-gray-900">{selectedSheet.name}</h4>
                <div className="overflow-x-auto max-h-[75vh] overflow-y-auto border border-gray-200 rounded-lg">
                  <table className="min-w-full text-sm">
                    <tbody>
                      {selectedSheet.rows.map((row, rowIndex) => (
                        <tr key={`${selectedSheet.name}-${rowIndex}`} className="border-b border-gray-100">
                          {row.map((cell, cellIndex) => (
                            <td key={`${rowIndex}-${cellIndex}`} className="px-3 py-2 text-gray-700">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-gray-500">
                  Всего строк: {selectedSheet.total_rows}
                </p>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={handleDownload}
            className="btn-primary"
          >
            Скачать
          </button>
        </div>
      </div>
    </Modal>
  )
}
