import { NavLink } from 'react-router-dom'
import useAuth from '@hooks/useAuth'
import {
  LayoutDashboard, Users, Swords, Shield,
  Settings, LogOut, Trophy
} from 'lucide-react'

const nav = [
  { to: '/',             icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/players',      icon: Users,            label: 'Jugadores' },
  { to: '/wars/current', icon: Swords,           label: 'Guerra actual' },
  { to: '/wars',         icon: Shield,           label: 'Historial guerras' },
]

const Sidebar = () => {
  const { user, isAdmin, logout } = useAuth()

  return (
    <aside className="fixed left-0 top-0 h-full w-[240px] glass border-r border-white/8 flex flex-col z-40">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/8">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-clan-gold/20 border border-clan-gold/40 flex items-center justify-center">
            <Trophy size={16} className="text-clan-gold" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-none">FamiliaPerfecta</p>
            <p className="text-[11px] text-white/40 mt-0.5">Clash of Clans</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                isActive
                  ? 'bg-clan-gold/15 text-clan-gold border border-clan-gold/25'
                  : 'text-white/50 hover:text-white/80 hover:bg-white/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={17} className={isActive ? 'text-clan-gold' : ''} />
                {label}
              </>
            )}
          </NavLink>
        ))}

        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all mt-2 ${
                isActive
                  ? 'bg-purple-500/15 text-purple-400 border border-purple-500/25'
                  : 'text-white/50 hover:text-white/80 hover:bg-white/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Settings size={17} className={isActive ? 'text-purple-400' : ''} />
                Administración
              </>
            )}
          </NavLink>
        )}
      </nav>

      {/* User footer */}
      <div className="px-3 pb-4 border-t border-white/8 pt-3">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg mb-1">
          <div className="w-7 h-7 rounded-full bg-clan-gold/20 border border-clan-gold/30 flex items-center justify-center text-xs font-medium text-clan-gold">
            {user?.username?.[0]?.toUpperCase() ?? '?'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.username ?? '—'}</p>
            <p className="text-[11px] text-white/40 truncate">{user?.role ?? 'member'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-white/40 hover:text-red-400 hover:bg-red-400/8 transition-all"
        >
          <LogOut size={15} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}

export default Sidebar