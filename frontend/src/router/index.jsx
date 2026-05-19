import { createBrowserRouter, Navigate } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'

// Layout
import AppLayout from '@components/layout/AppLayout'

// Pages — Auth
import Login from '@pages/auth/Login'

// Pages — App (lazy imports para mejor performance)
import { lazy, Suspense } from 'react'

import Register from '@pages/auth/Register'

const Dashboard   = lazy(() => import('@pages/dashboard/Dashboard'))
const PlayerList  = lazy(() => import('@pages/players/PlayerList'))
const PlayerProfile = lazy(() => import('@pages/players/PlayerProfile'))
const WarList     = lazy(() => import('@pages/wars/WarList'))
const CurrentWar  = lazy(() => import('@pages/wars/CurrentWar'))
const WarDetail   = lazy(() => import('@pages/wars/WarDetail'))
const AdminPanel  = lazy(() => import('@pages/admin/AdminPanel'))

const Loader = () => (
  <div className="flex items-center justify-center h-64">
    <div className="w-8 h-8 border-2 border-clan-gold border-t-transparent rounded-full animate-spin" />
  </div>
)

const withSuspense = (Component) => (
  <Suspense fallback={<Loader />}>
    <Component />
  </Suspense>
)

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },

  {
    path: '/register',
    element: <Register />,
  },

  // ── Rutas protegidas ───────────────────────────────────────────────────────
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true,            element: withSuspense(Dashboard) },
          { path: 'players',        element: withSuspense(PlayerList) },
          { path: 'players/:id',    element: withSuspense(PlayerProfile) },
          { path: 'wars',           element: withSuspense(WarList) },
          { path: 'wars/current',   element: withSuspense(CurrentWar) },
          { path: 'wars/:id',       element: withSuspense(WarDetail) },

          // Solo admins
          {
            element: <ProtectedRoute adminOnly />,
            children: [
              { path: 'admin', element: withSuspense(AdminPanel) },
            ],
          },
        ],
      },
    ],
  },

  // ── Fallback ───────────────────────────────────────────────────────────────
  { path: '*', element: <Navigate to="/" replace /> },
])

export default router