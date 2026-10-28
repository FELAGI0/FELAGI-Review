import api from './client'

export interface Comment {
  id: string
  pr_id: string
  user_id: string
  parent_id: string | null
  file_path: string | null
  line_number: number | null
  body: string
  resolved: boolean
  created_at: string
  updated_at: string
  author_username: string | null
}

export interface CommentThread {
  root: Comment
  replies: Comment[]
}

export interface CreateCommentInput {
  body: string
  file_path?: string | null
  line_number?: number | null
  parent_id?: string | null
}

export async function getComments(prId: string): Promise<CommentThread[]> {
  const { data } = await api.get<CommentThread[]>(`/prs/${prId}/comments`)
  return data
}

export async function createComment(
  prId: string,
  input: CreateCommentInput,
): Promise<Comment> {
  const { data } = await api.post<Comment>(`/prs/${prId}/comments`, input)
  return data
}

export async function updateComment(
  commentId: string,
  body: string,
): Promise<Comment> {
  const { data } = await api.patch<Comment>(`/comments/${commentId}`, { body })
  return data
}

export async function deleteComment(commentId: string): Promise<void> {
  await api.delete(`/comments/${commentId}`)
}

export async function resolveComment(
  commentId: string,
): Promise<{ id: string; resolved: boolean }> {
  const { data } = await api.post<{ id: string; resolved: boolean }>(
    `/comments/${commentId}/resolve`,
  )
  return data
}
