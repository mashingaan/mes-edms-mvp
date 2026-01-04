import { useQuery } from '@tanstack/react-query'
import { getSections } from '../../api/projects'
import { ProjectSection } from '../../types/project'

interface SectionSelectorProps {
  projectId: string
  selectedSectionId: string | null
  onSectionChange: (sectionId: string | null) => void
}

export function SectionSelector({
  projectId,
  selectedSectionId,
  onSectionChange,
}: SectionSelectorProps) {
  const { data: sections = [], isLoading } = useQuery({
    queryKey: ['sections', projectId],
    queryFn: () => getSections(projectId),
    enabled: !!projectId,
  })

  if (isLoading) {
    return (
      <div className="flex gap-2 mb-4">
        <div className="h-8 w-16 bg-gray-200 animate-pulse rounded-lg"></div>
        <div className="h-8 w-20 bg-gray-200 animate-pulse rounded-lg"></div>
      </div>
    )
  }

  const tabClass = (isActive: boolean) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-primary-600 text-white'
        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    }`

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <button
        onClick={() => onSectionChange(null)}
        className={tabClass(selectedSectionId === null)}
      >
        Все
      </button>
      
      {sections.map((section: ProjectSection) => (
        <button
          key={section.id}
          onClick={() => onSectionChange(section.id)}
          className={tabClass(selectedSectionId === section.id)}
        >
          {section.code}
        </button>
      ))}
      
      {sections.length > 0 && (
        <button
          onClick={() => onSectionChange('none')}
          className={tabClass(selectedSectionId === 'none')}
        >
          Без раздела
        </button>
      )}
    </div>
  )
}

