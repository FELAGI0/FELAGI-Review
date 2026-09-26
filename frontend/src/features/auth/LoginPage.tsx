import { useHealth } from '../../shared/useHealth'

export default function LoginPage() {
  const { data } = useHealth()
  return (
    <main className="login">
      <h1>ReviewHub</h1>
      <p>AI-powered code review for your team.</p>
      <a href="/api/auth/github/login">Login with GitHub</a>
      {data ? <small>API: {data.status}</small> : null}
    </main>
  )
}
