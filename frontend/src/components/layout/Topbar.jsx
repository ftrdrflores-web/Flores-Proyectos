import { useLocation } from 'react-router-dom'
import { Sun, Moon, Bell } from 'lucide-react'
import useTheme from '@hooks/useTheme'

const crumbs = {
  '/':             'Dashboard',
  '/players':      'Jugadores',
  '/wars':         'Historial de guerras',
  '/wars/current': 'Guerra actual',
  '/admin':        'Administración',
}

const Topbar = () => {
  const { isDark, toggleTheme } = useTheme()
  const location = useLocation()

  const title = crumbs[location.pathname] ?? 'FamiliaPerfecta'

  return (
    <header
      className="fixed top-0 right-0 h-[60px] glass border-b border-white/8 flex items-center px-6 gap-4 z-30"
      style={{ left: 240 }}
    >
      <h1 className="text-sm font-medium text-white/70 flex-1">{title}</h1>

      <div className="flex items-center gap-2">
        {/* Notificaciones — placeholder */}
        <button className="w-8 h-8 rounded-lg glass-sm flex items-center justify-center text-white/40 hover:text-white/70 transition-colors">
          <Bell size={15} />
        </button>

        {/* Dark/light toggle */}
        <button
          onClick={toggleTheme}
          className="w-8 h-8 rounded-lg glass-sm flex items-center justify-center text-white/40 hover:text-clan-gold transition-colors"
          aria-label="Cambiar tema"
        >
          {isDark ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  )
}

export default Topbar