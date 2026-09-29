import { useEffect, type ReactNode } from 'react'
import { useAuthStore } from '../shared/useAuthStore'
import { fetchMe, refresh } from '../shared/api/auth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const setAccessToken = useAuthStore((s) => s.setAccessToken)
  const setUser = useAuthStore((s) => s.setUser)
  const setLoading = useAuthStore((s) => s.setLoading)

  useEffect(() => {
    const init = async () => {
      const params = new URLSearchParams(window.location.search)
      const token = params.get('token')
      if (token) {
        setAccessToken(token)
        window.history.replaceState({}, '', window.location.pathname)
        try {
          setUser(await fetchMe())
        } catch {
          setAccessToken(null)
        }
      } else {
        try {
          setAccessToken(await refresh())
          setUser(await fetchMe())
        } catch {
          setAccessToken(null)
        }
      }
      setLoading(false)
    }
    init()
  }, [setAccessToken, setUser, setLoading])

  return <>{children}</>
}
