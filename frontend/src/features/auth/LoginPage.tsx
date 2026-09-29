import { useAuthStore } from '../../shared/useAuthStore'
import { login } from '../../shared/api/auth'

export default function LoginPage() {
  const user = useAuthStore((s) => s.user)

  if (user) {
    window.location.href = '/dashboard'
    return null
  }

  return (
    <main className="login">
      <img src="/favicon.svg" alt="" className="logo" width={64} height={64} />
      <h1>FELAGI-Review</h1>
      <p className="slogan">Your code deserves a felagi.</p>
      <button onClick={login}>Login with GitHub</button>
    </main>
  )
}
