import { clsx } from 'clsx'

interface ProgressBarProps {
  value: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function ProgressBar({ value, showLabel = true, size = 'md' }: ProgressBarProps) {
  const clampedValue = Math.max(0, Math.min(100, value))
  
  const heightClass = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }[size]
  
  return (
    <div className="flex items-center gap-3">
      <div className={clsx('flex-1 bg-gray-200 rounded-full overflow-hidden', heightClass)}>
        <div
          className={clsx(
            'h-full transition-all duration-300 rounded-full',
            clampedValue === 100 ? 'bg-green-500' : 'bg-primary-500'
          )}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-gray-700 min-w-[3rem] text-right">
          {clampedValue}%
        </span>
      )}
    </div>
  )
}

