import api from './client'

export interface Repository {
  id: string
  full_name: string
  github_id: number | null
  installation_id: number | null
  auto_review_enabled: boolean
}

export interface PullRequest {
  id: string
  repo_id: string
  github_id: number | null
  number: number
  title: string
  description: string | null
  author_login: string
  base_branch: string
  head_branch: string
  state: 'open' | 'closed' | 'merged'
  additions: number
  deletions: number
  files_changed: number
  diff_url: string | null
  created_at: string
  updated_at: string
}

export interface DiffLine {
  type: 'add' | 'del' | 'context' | 'meta'
  new_number: number | null
  old_number: number | null
  content: string
}

export interface DiffHunk {
  old_start: number
  new_start: number
  lines: DiffLine[]
}

export interface DiffFile {
  path: string
  old_path: string
  status: string
  additions: number
  deletions: number
  is_binary: boolean
  hunks: DiffHunk[]
}

export interface DiffResponse {
  pull_number: number
  files: DiffFile[]
}

export async function fetchRepositories(): Promise<Repository[]> {
  const { data } = await api.get<Repository[]>('/repositories')
  return data
}

export async function fetchAppInstallUrl(): Promise<string> {
  const { data } = await api.get<{ install_url: string }>('/github-app/install-url')
  return data.install_url
}

export async function syncInstallations(): Promise<{
  installations: number
  repositories: number
}> {
  const { data } = await api.post<{ installations: number; repositories: number }>(
    '/github-app/sync',
  )
  return data
}

export async function fetchPullRequests(
  repoId: string,
  state?: 'open' | 'closed' | 'merged' | null,
): Promise<PullRequest[]> {
  const params = state ? { state } : {}
  const { data } = await api.get<PullRequest[]>(`/repositories/${repoId}/pulls`, { params })
  return data
}

export async function fetchPullRequest(
  repoId: string,
  number: number,
): Promise<PullRequest> {
  const { data } = await api.get<PullRequest>(`/repositories/${repoId}/pulls/${number}`)
  return data
}

export async function fetchPullRequestDiff(
  repoId: string,
  number: number,
): Promise<DiffResponse> {
  const { data } = await api.get<DiffResponse>(
    `/repositories/${repoId}/pulls/${number}/diff`,
  )
  return data
}
