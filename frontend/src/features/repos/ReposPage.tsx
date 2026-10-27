import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../shared/useAuthStore'
import {
  fetchAppInstallUrl,
  fetchRepositories,
  syncInstallations,
} from '../../shared/api/repos'

export default function ReposPage() {
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()
  const { data: repos, isLoading, error } = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })
  const { data: installUrl } = useQuery({
    queryKey: ['app-install-url'],
    queryFn: fetchAppInstallUrl,
  })
  const syncMutation = useMutation({
    mutationFn: syncInstallations,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['repositories'] }),
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
          <div className="header-actions">
            <button
              className="btn-secondary"
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
            >
              {syncMutation.isPending ? 'Syncing...' : 'Sync now'}
            </button>
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
        </div>
        {syncMutation.isError && (
          <div className="error-box">Sync failed</div>
        )}
        {syncMutation.isSuccess && (
          <div className="success-box">
            Synced {syncMutation.data.repositories} repositories from{' '}
            {syncMutation.data.installations} installation(s)
          </div>
        )}

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
