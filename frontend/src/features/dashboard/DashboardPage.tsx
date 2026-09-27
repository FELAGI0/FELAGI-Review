import { useHealth } from '../../shared/useHealth'

export default function DashboardPage() {
  const { data } = useHealth()
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/favicon.svg" alt="" width={28} height={28} />
          <span>FELAGI-Review</span>
        </div>
      </aside>
      <main className="dashboard">
        <h1>Dashboard</h1>
        <p>Open PRs, pending reviews and AI findings will appear here.</p>
        {data ? <small>API: {data.status}</small> : null}
      </main>
    </div>
  )
}
