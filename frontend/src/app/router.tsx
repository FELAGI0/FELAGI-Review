import { createBrowserRouter } from 'react-router-dom'
import LoginPage from '../features/auth/LoginPage'
import AuthCallback from '../features/auth/AuthCallback'
import DashboardPage from '../features/dashboard/DashboardPage'
import ReposPage from '../features/repos/ReposPage'
import PullsPage from '../features/repos/PullsPage'
import PrDetailPage from '../features/prs/PrDetailPage'
import { AppLayout } from './AppLayout'
import { ProtectedRoute } from './ProtectedRoute'

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <AppLayout>
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      </AppLayout>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <AppLayout>
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      </AppLayout>
    ),
  },
  {
    path: '/repos',
    element: (
      <AppLayout>
        <ProtectedRoute>
          <ReposPage />
        </ProtectedRoute>
      </AppLayout>
    ),
  },
  {
    path: '/repos/:repoId',
    element: (
      <AppLayout>
        <ProtectedRoute>
          <PullsPage />
        </ProtectedRoute>
      </AppLayout>
    ),
  },
  {
    path: '/repos/:repoId/pulls/:number',
    element: (
      <AppLayout>
        <ProtectedRoute>
          <PrDetailPage />
        </ProtectedRoute>
      </AppLayout>
    ),
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/auth/callback',
    element: <AuthCallback />,
  },
])
