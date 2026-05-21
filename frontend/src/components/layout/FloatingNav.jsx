import { useState, useEffect, useRef } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { gsap } from 'gsap'
import { useGSAP } from '@gsap/react'
import {
  LayoutDashboard, Users, Swords, Shield,
  Settings, LogOut, Trophy, Sun, Moon, Bell
} from 'lucide-react'
import useAuth from '@hooks/useAuth'
import useTheme from '@hooks/useTheme'

const NAV_ITEMS = [
  { to: '/',             icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/players',      icon: Users,            label: 'Jugadores' },
  { to: '/wars/current', icon: Swords,           label: 'Guerra' },
  { to: '/wars',         icon: Shield,           label: 'Historial' },
]

const FloatingNav = () => {
  const { user, isAdmin, logout } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const [visible, setVisible] = useState(false)
  const [pinned, setPinned]   = useState(false)
  const navRef  = useRef(null)
  const timerRef = useRef(null)

  // Mouse proximity detection
  useEffect(() => {
    const handleMouseMove = (e) => {
      const threshold = window.innerHeight - 100
      if (e.clientY > threshold) {
        clearTimeout(timerRef.current)
        setVisible(true)
      } else if (!pinned) {
        timerRef.current = setTimeout(() => setVisible(false), 1200)
      }
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      clearTimeout(timerRef.current)
    }
  }, [pinned])

  // GSAP show/hide animation
  useGSAP(() => {
    gsap.to(navRef.current, {
      y:        visible ? 0 : 80,
      opacity:  visible ? 1 : 0,
      duration: 0.35,
      ease:     visible ? 'back.out(1.4)' : 'power2.in',
    })
  }, { dependencies: [visible], scope: navRef })

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div
      ref={navRef}
      className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 opacity-0 translate-y-20"
      onMouseEnter={() => { clearTimeout(timerRef.current); setVisible(true) }}
      onMouseLeave={() => { if (!pinned) timerRef.current = setTimeout(() => setVisible(false), 800) }}
    >
      <div
        className="flex items-center gap-1 px-3 py-2 rounded-2xl border border-white/10 shadow-glass"
        style={{
          background: 'linear-gradient(135deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.03) 100%)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-2 mr-1 border-r border-white/10 pr-3">
          <div className="w-6 h-6 rounded-lg bg-white/10 flex items-center justify-center">
            <Trophy size={13} className="text-white/70" />
          </div>
          <span className="text-xs font-medium text-white/50 hidden sm:block">FP</span>
        </div>

        {/* Nav items */}
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `relative flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-white/12 text-white'
                  : 'text-white/40 hover:text-white/70 hover:bg-white/6'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={17} />
                <span className="text-[10px] font-medium">{label}</span>
                {isActive && (
                  <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-white/60" />
                )}
              </>
            )}
          </NavLink>
        ))}

        {/* Divider */}
        <div className="w-px h-8 bg-white/10 mx-1" />

        {/* Actions */}
        <button
          onClick={toggleTheme}
          className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl text-white/40 hover:text-white/70 hover:bg-white/6 transition-all"
        >
          {isDark ? <Sun size={17} /> : <Moon size={17} />}
          <span className="text-[10px]">Tema</span>
        </button>

        <button className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl text-white/40 hover:text-white/70 hover:bg-white/6 transition-all relative">
          <Bell size={17} />
          <span className="text-[10px]">Avisos</span>
          <span className="absolute top-1 right-2 w-1.5 h-1.5 rounded-full bg-red-400" />
        </button>

        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-all ${
                isActive ? 'bg-white/12 text-white' : 'text-white/40 hover:text-white/70 hover:bg-white/6'
              }`
            }
          >
            <Settings size={17} />
            <span className="text-[10px]">Admin</span>
          </NavLink>
        )}

        {/* Divider */}
        <div className="w-px h-8 bg-white/10 mx-1" />

        {/* User + logout */}
        <div className="flex items-center gap-2 pl-1">
          <div className="w-6 h-6 rounded-full bg-white/10 border border-white/15 flex items-center justify-center text-[10px] font-medium text-white/60">
            {user?.username?.[0]?.toUpperCase() ?? '?'}
          </div>
          <button
            onClick={handleLogout}
            className="flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-xl text-white/30 hover:text-red-400 hover:bg-red-400/8 transition-all"
          >
            <LogOut size={15} />
            <span className="text-[10px]">Salir</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default FloatingNav
