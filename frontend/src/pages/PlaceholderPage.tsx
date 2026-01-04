import { Construction } from 'lucide-react'

interface PlaceholderPageProps {
  title: string
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <Construction className="h-16 w-16 text-gray-400 mb-4" />
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
      <p className="text-gray-500">Раздел в разработке</p>
    </div>
  )
}

