import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../shared/useAuthStore'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user)
  const isLoading = useAuthStore((s) => s.isLoading)

  if (isLoading) {
    return <div className="spinner" aria-label="Loading" />
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
