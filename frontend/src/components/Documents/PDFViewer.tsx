import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { X, AlertCircle } from 'lucide-react'
import apiClient from '../../api/client'

interface PDFViewerProps {
  url: string | null
  onClose: () => void
}

export function PDFViewer({ url, onClose }: PDFViewerProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (url) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [url, onClose])

  useEffect(() => {
    if (!url) {
      setBlobUrl(null)
      return
    }

    let objectUrl: string | null = null
    let cancelled = false

    setLoading(true)
    setError(null)
    setBlobUrl(null)

    apiClient
      .get<Blob>(url, { responseType: 'blob' })
      .then((res) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(res.data)
        setBlobUrl(objectUrl)
      })
      .catch((err) => {
        if (cancelled) return

        const status = err?.response?.status
        const detail = err?.response?.data?.detail
        const message = detail || err?.message

        const statusText = status ? ` (HTTP ${status})` : ''
        const messageText = message ? `: ${message}` : ''
        setError(`Не удалось загрузить PDF${statusText}${messageText}`)
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [url])

  if (!url) return null

  return createPortal(
    <div className="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center">
      <button
        onClick={onClose}
        className="absolute top-4 right-4 p-2 bg-white rounded-full hover:bg-gray-100 z-10"
      >
        <X className="h-6 w-6" />
      </button>

      <div className="w-full h-full max-w-6xl max-h-[90vh] m-4">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center h-full text-white">
            <AlertCircle className="h-16 w-16 mb-4" />
            <p className="text-lg">{error}</p>
          </div>
        )}

        {blobUrl && !error && (
          <iframe
            src={blobUrl}
            className="w-full h-full bg-white rounded-lg"
            title="PDF Preview"
          />
        )}
      </div>
    </div>,
    document.body
  )
}

