import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../shared/useAuthStore'
import {
  createComment,
  deleteComment,
  getComments,
  resolveComment,
  type CommentThread as ThreadData,
  type CreateCommentInput,
} from '../../shared/api/comments'
import CommentThread from './CommentThread'

interface Props {
  prId: string
}

export default function CommentsPanel({ prId }: Props) {
  const user = useAuthStore((s) => s.user)
  const queryClient = useQueryClient()
  const [generalBody, setGeneralBody] = useState('')

  const { data: threads, isLoading, error } = useQuery({
    queryKey: ['comments', prId],
    queryFn: () => getComments(prId),
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['comments', prId] })

  const createMutation = useMutation({
    mutationFn: (input: CreateCommentInput) => createComment(prId, input),
    onSuccess: invalidate,
  })

  const replyMutation = useMutation({
    mutationFn: ({ parentId, body }: { parentId: string; body: string }) =>
      createComment(prId, { body, parent_id: parentId }),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteComment,
    onSuccess: invalidate,
  })

  const resolveMutation = useMutation({
    mutationFn: resolveComment,
    onSuccess: invalidate,
  })

  const submitGeneral = async () => {
    if (!generalBody.trim()) return
    await createMutation.mutateAsync({ body: generalBody.trim() })
    setGeneralBody('')
  }

  const generalThreads: ThreadData[] = (threads ?? []).filter(
    (t) => !t.root.file_path,
  )

  return (
    <div className="comments-panel">
      <h2>Discussion</h2>

      {isLoading && <div className="comments-loading">Loading comments...</div>}
      {error && <div className="error-box">Failed to load comments</div>}

      <div className="comment-new">
        <textarea
          value={generalBody}
          onChange={(e) => setGeneralBody(e.target.value)}
          placeholder="Leave a general comment on this PR..."
          rows={2}
        />
        <div className="comment-form-actions">
          <button
            className="btn-primary btn-sm"
            onClick={submitGeneral}
            disabled={createMutation.isPending || !generalBody.trim()}
          >
            {createMutation.isPending ? 'Sending...' : 'Comment'}
          </button>
        </div>
      </div>

      {generalThreads.length === 0 && !isLoading && (
        <div className="comments-empty">No comments yet</div>
      )}

      {generalThreads.map((thread) => (
        <CommentThread
          key={thread.root.id}
          thread={thread}
          currentUserId={user?.id ?? null}
          onReply={async (parentId, body) => {
            await replyMutation.mutateAsync({ parentId, body })
          }}
          onDelete={async (id) => {
            await deleteMutation.mutateAsync(id)
          }}
          onResolve={async (id) => {
            await resolveMutation.mutateAsync(id)
          }}
        />
      ))}
    </div>
  )
}
