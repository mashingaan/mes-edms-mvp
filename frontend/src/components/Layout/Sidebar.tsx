import { NavLink } from 'react-router-dom'
import { 
  FileText, 
  Settings, 
  ShoppingCart, 
  Factory, 
  CheckCircle, 
  Truck,
  LayoutDashboard 
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { to: '/', label: 'Конструкторский', icon: FileText, active: true },
  { to: '/tech', label: 'Технологический', icon: Settings, disabled: false },
  { to: '/procurement', label: 'Закупка', icon: ShoppingCart, disabled: true },
  { to: '/production', label: 'Производство', icon: Factory, disabled: true },
  { to: '/qc', label: 'ОТК', icon: CheckCircle, disabled: true },
  { to: '/shipping', label: 'Отгрузка', icon: Truck, disabled: true },
]

export function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6">
        <div className="flex items-center gap-2">
          <LayoutDashboard className="h-8 w-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">MES-EDMS</span>
        </div>
      </div>
      
      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              item.disabled && 'opacity-50 cursor-not-allowed',
              isActive && !item.disabled
                ? 'bg-primary-50 text-primary-700'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            )}
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          Phase 1 MVP
        </p>
      </div>
    </aside>
  )
}

