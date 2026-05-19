import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { gsap } from 'gsap'
import { useGSAP } from '@gsap/react'
import { sileo } from 'sileo'
import { Eye, EyeOff, Trophy, Loader2, ArrowLeft } from 'lucide-react'
import useAuthStore from '@store/authStore'
import authService from '@services/authService'

const FIELDS = [
  { name: 'clan_tag',          label: 'Clan tag',          placeholder: '#2C29G2RJL', type: 'text' },
  { name: 'player_tag',        label: 'Player tag',        placeholder: '#28L8RL8QG', type: 'text' },
  { name: 'username',          label: 'Usuario',           placeholder: 'tu_usuario', type: 'text' },
  { name: 'email',             label: 'Correo',            placeholder: 'correo@ejemplo.com', type: 'email' },
  { name: 'first_name',        label: 'Nombre',            placeholder: 'Omar',       type: 'text' },
  { name: 'last_name',         label: 'Apellido',          placeholder: 'Flores',     type: 'text' },
  { name: 'password',          label: 'Contraseña',        placeholder: '••••••••',   type: 'password' },
  { name: 'password_confirm',  label: 'Confirmar contraseña', placeholder: '••••••••', type: 'password' },
]

const Register = () => {
  const navigate   = useNavigate()
  const login      = useAuthStore((s) => s.login)

  const [form, setForm]         = useState({
    clan_tag: '', player_tag: '', username: '', email: '',
    first_name: '', last_name: '', password: '', password_confirm: '',
  })
  const [showPass, setShowPass] = useState({ password: false, password_confirm: false })
  const [loading, setLoading]   = useState(false)

  const containerRef = useRef(null)
  const cardRef      = useRef(null)

  useGSAP(() => {
    gsap.timeline()
      .from(containerRef.current, { opacity: 0, duration: 0.5 })
      .from(cardRef.current,      { y: 30, opacity: 0, duration: 0.5, ease: 'power3.out' }, '-=0.2')
  }, { scope: containerRef })

  const handleChange = (e) => setForm((p) => ({ ...p, [e.target.name]: e.target.value }))

  const togglePass = (name) => setShowPass((p) => ({ ...p, [name]: !p[name] }))

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (form.password !== form.password_confirm) {
      sileo.error({ title: 'Error', description: 'Las contraseñas no coinciden.' })
      return
    }

    setLoading(true)
    try {
      const { data } = await authService.register(form)

      // Guardar tokens y datos en el store
      localStorage.setItem('access_token',  data.access)
      localStorage.setItem('refresh_token', data.refresh)
      useAuthStore.setState({
        user:         data.user,
        accessToken:  data.access,
        refreshToken: data.refresh,
      })

      sileo.success({ title: '¡Cuenta creada!', description: `Bienvenido, ${data.user.username}` })
      navigate('/', { replace: true })

    } catch (err) {
      const errors = err.response?.data
      // Mostrar el primer error que venga del backend
      const first = errors
        ? Object.values(errors).flat()[0]
        : 'Error al crear la cuenta.'
      sileo.error({ title: 'Error de registro', description: first })

      gsap.to(cardRef.current, {
        x: [-8, 8, -5, 5, 0],
        duration: 0.4,
        ease: 'power1.inOut',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-clan-dark flex items-center justify-center px-4 py-10 relative overflow-hidden"
    >
      {/* Fondo decorativo */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-clan-gold/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-clan-red/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 mx-auto rounded-xl bg-clan-gold/15 border border-clan-gold/30 flex items-center justify-center mb-3">
            <Trophy size={22} className="text-clan-gold" />
          </div>
          <h1 className="text-xl font-semibold">Crear cuenta</h1>
          <p className="text-xs text-white/40 mt-1">Únete a tu clan en FamiliaPerfecta Stats</p>
        </div>

        {/* Card */}
        <div ref={cardRef} className="card border border-white/10 shadow-glass">
          <form onSubmit={handleSubmit} className="space-y-3">

            {FIELDS.map(({ name, label, placeholder, type }) => {
              const isPass = type === 'password'
              const shown  = showPass[name]
              return (
                <div key={name}>
                  <label className="block text-xs font-medium text-white/60 mb-1">
                    {label}
                    {name === 'player_tag' && (
                      <span className="ml-1 text-white/30 font-normal">— determina tu rol automáticamente</span>
                    )}
                  </label>
                  <div className="relative">
                    <input
                      type={isPass ? (shown ? 'text' : 'password') : type}
                      name={name}
                      value={form[name]}
                      onChange={handleChange}
                      placeholder={placeholder}
                      required={name !== 'player_tag'}
                      disabled={loading}
                      className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-white/20 focus:outline-none focus:border-clan-gold/50 transition-all disabled:opacity-50"
                    />
                    {isPass && (
                      <button
                        type="button"
                        onClick={() => togglePass(name)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                        tabIndex={-1}
                      >
                        {shown ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Nota de rol */}
            <div className="text-[11px] text-white/30 bg-white/3 border border-white/8 rounded-lg px-3 py-2 leading-relaxed">
              Tu rol se asigna automáticamente: <span className="text-clan-gold/70">Líder / Co-Líder → Admin</span> · Elder / Miembro → Member
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-clan-gold text-clan-dark text-sm font-semibold hover:bg-clan-gold/90 active:scale-[0.98] transition-all disabled:opacity-60 flex items-center justify-center gap-2 mt-1"
            >
              {loading ? <><Loader2 size={14} className="animate-spin" /> Creando cuenta...</> : 'Crear cuenta'}
            </button>
          </form>

          <div className="h-px bg-white/8 my-4" />

          <Link
            to="/login"
            className="flex items-center justify-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors"
          >
            <ArrowLeft size={13} />
            Ya tengo cuenta — Iniciar sesión
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Register