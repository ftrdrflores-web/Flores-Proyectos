import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import authService from '@services/authService'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user:         null,
      accessToken:  null,
      refreshToken: null,
      isLoading:    false,
      error:        null,

      // ── Computed ─────────────────────────────────────────────────────────
      isAuthenticated: () => !!get().accessToken,
      isAdmin: () => get().user?.role === 'admin',

      // ── Actions ──────────────────────────────────────────────────────────
      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const { data } = await authService.login(credentials)
          localStorage.setItem('access_token',  data.access)
          localStorage.setItem('refresh_token', data.refresh)
          set({
            user:         data.user,
            accessToken:  data.access,
            refreshToken: data.refresh,
            isLoading:    false,
            error:        null,
          })
          return { success: true }
        } catch (err) {
          const message = err.response?.data?.detail || 'Credenciales incorrectas'
          set({ isLoading: false, error: message })
          return { success: false, error: message }
        }
      },

      logout: async () => {
        try {
          const refresh = get().refreshToken
          if (refresh) await authService.logout(refresh)
        } catch (_) {
          // silencioso — limpiar de todas formas
        } finally {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({ user: null, accessToken: null, refreshToken: null })
        }
      },

      fetchMe: async () => {
        try {
          const { data } = await authService.me()
          set({ user: data })
        } catch (_) {
          get().logout()
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'fp-auth',
      partialize: (state) => ({
        user:         state.user,
        accessToken:  state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)

export default useAuthStore