import useAuthStore from '@store/authStore'

const useAuth = () => {
  const user         = useAuthStore((s) => s.user)
  const isLoading    = useAuthStore((s) => s.isLoading)
  const error        = useAuthStore((s) => s.error)
  const login        = useAuthStore((s) => s.login)
  const logout       = useAuthStore((s) => s.logout)
  const fetchMe      = useAuthStore((s) => s.fetchMe)
  const clearError   = useAuthStore((s) => s.clearError)
  const accessToken  = useAuthStore((s) => s.accessToken)

  const isAuthenticated = !!accessToken
  const isAdmin = user?.role === 'admin'

  return { user, isLoading, error, login, logout, fetchMe, clearError, isAuthenticated, isAdmin }
}

export default useAuth