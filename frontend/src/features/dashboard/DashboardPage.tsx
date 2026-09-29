import { useAuthStore } from '../../shared/useAuthStore'
import { logout } from '../../shared/api/auth'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/favicon.svg" alt="" width={28} height={28} />
          <span>FELAGI-Review</span>
        </div>
        {user && (
          <div className="user-info">
            <img src={user.avatar_url ?? undefined} alt="" width={32} height={32} />
            <span>{user.username}</span>
            <button onClick={() => logout().then(() => (window.location.href = '/login'))}>
              Logout
            </button>
          </div>
        )}
      </aside>
      <main className="dashboard">
        <h1>Welcome back, {user?.username}</h1>
      </main>
    </div>
  )
}
