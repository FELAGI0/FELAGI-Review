import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useAuthStore } from '../../shared/useAuthStore'
import {
  fetchPullRequest,
  fetchPullRequestDiff,
  type DiffFile,
} from '../../shared/api/repos'
import DiffViewer from './DiffViewer'

export default function PrDetailPage() {
  const { repoId, number } = useParams<{ repoId: string; number: string }>()
  const user = useAuthStore((s) => s.user)
  const prNumber = number ? parseInt(number, 10) : null
  const [selectedFile, setSelectedFile] = useState<DiffFile | null>(null)

  const { data: pr, isLoading: prLoading, error: prError } = useQuery({
    queryKey: ['pr', repoId, prNumber],
    queryFn: () => fetchPullRequest(repoId!, prNumber!),
    enabled: !!repoId && !!prNumber,
  })

  const { data: diff, isLoading: diffLoading, error: diffError } = useQuery({
    queryKey: ['pr-diff', repoId, prNumber],
    queryFn: () => fetchPullRequestDiff(repoId!, prNumber!),
    enabled: !!repoId && !!prNumber,
  })

  const activeFile = selectedFile ?? diff?.files[0] ?? null

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
          {repoId && <Link to={`/repos/${repoId}`}>Pull Requests</Link>}
        </nav>
      </aside>
      <main className="page pr-detail">
        {prLoading && <div className="spinner" />}
        {prError && <div className="error-box">Failed to load pull request</div>}

        {pr && (
          <div className="pr-header">
            <h1>
              {pr.title} <span className="pr-number">#{pr.number}</span>
            </h1>
            <div className="pr-header-meta">
              <span className={`pr-state pr-state-${pr.state}`}>{pr.state}</span>
              <span>by {pr.author_login}</span>
              <span className="pr-branches">
                {pr.base_branch} &lt;- {pr.head_branch}
              </span>
              <span>
                <span className="diff-add">+{pr.additions}</span>{' '}
                <span className="diff-del">-{pr.deletions}</span>
              </span>
              <span>{pr.files_changed} files</span>
              {pr.github_id && pr.diff_url && (
                <a
                  href={pr.diff_url.replace(/\.diff$/, '')}
                  target="_blank"
                  rel="noreferrer"
                >
                  View on GitHub
                </a>
              )}
            </div>
          </div>
        )}

        <div className="pr-layout">
          <div className="file-tree">
            <div className="file-tree-header">Files ({diff?.files.length ?? 0})</div>
            {diffLoading && <div className="file-tree-loading">Loading diff...</div>}
            {diffError && (
              <div className="error-box">Failed to load diff</div>
            )}
            <ul>
              {diff?.files.map((file) => (
                <li
                  key={file.path}
                  className={
                    activeFile?.path === file.path ? 'file-item active' : 'file-item'
                  }
                  onClick={() => setSelectedFile(file)}
                >
                  <span className="file-item-path" title={file.path}>
                    {file.path}
                  </span>
                  <span className="file-item-stats">
                    <span className="diff-add">+{file.additions}</span>
                    <span className="diff-del">-{file.deletions}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="diff-pane">
            {activeFile && <DiffViewer file={activeFile} />}
            {!diffLoading && !activeFile && !diffError && (
              <div className="empty-state">
                <p>No changed files.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
