import { useHealth } from '../../shared/useHealth'

export default function LoginPage() {
  const { data } = useHealth()
  return (
    <main className="login">
      <img src="/favicon.svg" alt="" className="logo" width={64} height={64} />
      <h1>FELAGI-Review</h1>
      <p className="slogan">Your code deserves a felagi.</p>
      <a href="/api/auth/github/login">Login with GitHub</a>
      {data ? <small>API: {data.status}</small> : null}
    </main>
  )
}
