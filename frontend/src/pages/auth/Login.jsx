import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { gsap } from 'gsap'
import { useGSAP } from '@gsap/react'
import { sileo } from 'sileo'
import { Eye, EyeOff, Trophy, Loader2 } from 'lucide-react'
import useAuth from '@hooks/useAuth'
import {Link} from 'react-router-dom'

gsap.registerPlugin()

const Login = () => {
  const navigate = useNavigate()
  const { login, isAuthenticated, isLoading, clearError } = useAuth()

  const [form, setForm]         = useState({ username: '', password: '' })
  const [showPass, setShowPass] = useState(false)

  // Refs para GSAP
  const containerRef = useRef(null)
  const cardRef      = useRef(null)
  const logoRef      = useRef(null)
  const fieldsRef    = useRef(null)

  // Si ya está autenticado, redirige
  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
    return () => clearError()
  }, [isAuthenticated, navigate, clearError])

  // Animación de entrada con GSAP
  useGSAP(() => {
    const tl = gsap.timeline()

    tl.from(containerRef.current, {
      opacity: 0,
      duration: 0.6,
      ease: 'power2.out',
    })
    .from(logoRef.current, {
      y: -30,
      opacity: 0,
      duration: 0.7,
      ease: 'back.out(1.4)',
    }, '-=0.2')
    .from(cardRef.current, {
      y: 40,
      opacity: 0,
      duration: 0.6,
      ease: 'power3.out',
    }, '-=0.4')
    .from(
      fieldsRef.current?.children ?? [],
      {
        y: 20,
        opacity: 0,
        duration: 0.4,
        stagger: 0.08,
        ease: 'power2.out',
      },
      '-=0.2'
    )
  }, { scope: containerRef })

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!form.username.trim() || !form.password.trim()) {
      sileo.warning({ title: 'Campos requeridos', description: 'Ingresa tu usuario y contraseña.' })
      return
    }

    const result = await login(form)

    if (result.success) {
      sileo.success({ title: '¡Bienvenido de vuelta!', description: `Hola, ${form.username}` })
      navigate('/', { replace: true })
    } else {
      sileo.error({
        title: 'Error al iniciar sesión',
        description: result.error ?? 'Verifica tus credenciales.',
      })
      // Shake animation en el card
      gsap.to(cardRef.current, {
        x: [-8, 8, -6, 6, -3, 3, 0],
        duration: 0.5,
        ease: 'power1.inOut',
      })
    }
  }

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-clan-dark flex items-center justify-center px-4 relative overflow-hidden"
    >
      {/* Fondo decorativo */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-clan-gold/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-clan-red/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-sm relative z-10">
        {/* Logo / Header */}
        <div ref={logoRef} className="text-center mb-8">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-clan-gold/15 border border-clan-gold/30 flex items-center justify-center mb-4 animate-pulse-gold">
            <Trophy size={26} className="text-clan-gold" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">FamiliaPerfecta</h1>
          <p className="text-sm text-white/40 mt-1">Stats — Clash of Clans</p>
        </div>

        {/* Card glass */}
        <div ref={cardRef} className="card border border-white/10 shadow-glass">
          <div ref={fieldsRef}>
            <div className="mb-1">
              <h2 className="text-base font-medium">Iniciar sesión</h2>
              <p className="text-xs text-white/40 mt-0.5">Accede con tu cuenta del clan</p>
            </div>

            <div className="h-px bg-white/8 my-4" />

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Usuario */}
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">
                  Usuario
                </label>
                <input
                  type="text"
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  placeholder="tu_usuario"
                  autoComplete="username"
                  disabled={isLoading}
                  className="w-full px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-clan-gold/50 focus:bg-white/8 transition-all disabled:opacity-50"
                />
              </div>

              {/* Contraseña */}
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    name="password"
                    value={form.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    disabled={isLoading}
                    className="w-full px-3 py-2.5 pr-10 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-clan-gold/50 focus:bg-white/8 transition-all disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                    tabIndex={-1}
                  >
                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-lg bg-clan-gold text-clan-dark text-sm font-semibold hover:bg-clan-gold/90 active:scale-[0.98] transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    Entrando...
                  </>
                ) : (
                  'Entrar al clan'
                )}
              </button>
            </form>
          </div>
        </div>
        <Link to="/register" className="flex items-center justify-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors">
        ¿No tienes cuenta? Regístrate
        </Link>

        <p className="text-center text-xs text-white/20 mt-6">
          Solo miembros de FamiliaPerfecta pueden acceder
        </p>
      </div>
    </div>
  )
}

export default Login