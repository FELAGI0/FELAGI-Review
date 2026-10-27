import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../shared/useAuthStore'
import { fetchAppInstallUrl, fetchRepositories } from '../../shared/api/repos'

export default function ReposPage() {
  const user = useAuthStore((s) => s.user)
  const { data: repos, isLoading, error } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })
  const { data: installUrl } = useQuery({
    queryKey: ['app-install-url'],
    queryFn: fetchAppInstallUrl,
  })

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
          </div>
        )}
        <nav className="nav-links">
          <Link to="/repos">Repositories</Link>
        </nav>
      </aside>
      <main className="page">
        <div className="page-header">
          <h1>Repositories</h1>
          {installUrl && (
            <a
              className="btn-primary"
              href={installUrl}
              target="_blank"
              rel="noreferrer"
            >
              Connect GitHub
            </a>
          )}
        </div>

        {isLoading && <div className="spinner" />}
        {error && <div className="error-box">Failed to load repositories</div>}

        {repos && repos.length === 0 && (
          <div className="empty-state">
            <p>No repositories connected yet.</p>
            <p>
              Install the FELAGI-Review GitHub App to start tracking pull requests.
            </p>
          </div>
        )}

        {repos && repos.length > 0 && (
          <ul className="repo-list">
            {repos.map((repo) => (
              <li key={repo.id} className="repo-card">
                <Link to={`/repos/${repo.id}`} className="repo-link">
                  <span className="repo-name">{repo.full_name}</span>
                  <span className="repo-meta">
                    {repo.installation_id ? 'connected' : 'not connected'}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
