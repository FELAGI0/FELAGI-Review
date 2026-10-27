import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useAuthStore } from '../../shared/useAuthStore'
import { fetchPullRequests } from '../../shared/api/repos'

type StateFilter = 'all' | 'open' | 'closed'

const FILTERS: StateFilter[] = ['all', 'open', 'closed']

export default function PullsPage() {
  const { repoId } = useParams<{ repoId: string }>()
  const user = useAuthStore((s) => s.user)
  const [filter, setFilter] = useState<StateFilter>('all')

  const { data: pulls, isLoading, error } = useQuery({
    queryKey: ['pulls', repoId, filter],
    queryFn: () => fetchPullRequests(repoId!, filter === 'all' ? null : filter),
    enabled: !!repoId,
  })

  const visible = pulls?.filter((pr) => {
    if (filter === 'all') return true
    if (filter === 'open') return pr.state === 'open'
    return pr.state === 'closed' || pr.state === 'merged'
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
          <h1>Pull Requests</h1>
          <div className="filter-tabs">
            {FILTERS.map((f) => (
              <button
                key={f}
                className={filter === f ? 'filter-tab active' : 'filter-tab'}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {isLoading && <div className="spinner" />}
        {error && <div className="error-box">Failed to load pull requests</div>}

        {visible && visible.length === 0 && (
          <div className="empty-state">
            <p>No pull requests found.</p>
          </div>
        )}

        <ul className="pr-list">
          {visible?.map((pr) => (
            <li key={pr.id} className="pr-card">
              <Link to={`/repos/${repoId}/pulls/${pr.number}`} className="pr-link">
                <div className="pr-title-line">
                  <span
                    className={`pr-state pr-state-${pr.state}`}
                  >
                    {pr.state}
                  </span>
                  <span className="pr-title">
                    {pr.title}
                  </span>
                  <span className="pr-number">#{pr.number}</span>
                </div>
                <div className="pr-meta-line">
                  <span>by {pr.author_login}</span>
                  <span>
                    <span className="diff-add">+{pr.additions}</span>{' '}
                    <span className="diff-del">-{pr.deletions}</span>
                  </span>
                  <span>{pr.files_changed} files</span>
                  <span>{new Date(pr.updated_at).toLocaleDateString()}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </main>
    </div>
  )
}
