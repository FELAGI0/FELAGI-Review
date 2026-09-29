import { Navigate, useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '../../shared/useAuthStore'

export default function AuthCallback() {
  const [params] = useSearchParams()
  const setAccessToken = useAuthStore((s) => s.setAccessToken)

  useEffect(() => {
    const token = params.get('token')
    if (token) setAccessToken(token)
  }, [params, setAccessToken])

  return <Navigate to="/dashboard" replace />
}
