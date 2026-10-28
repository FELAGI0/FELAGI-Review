import { useState } from 'react'
import type { Comment, CommentThread as ThreadData } from '../../shared/api/comments'

interface Props {
  thread: ThreadData
  currentUserId: string | null
  onReply: (parentId: string, body: string) => Promise<void>
  onDelete: (commentId: string) => Promise<void>
  onResolve: (commentId: string) => Promise<void>
}

function CommentBody({
  comment,
  currentUserId,
  isRoot,
  onDelete,
  onResolve,
}: {
  comment: Comment
  currentUserId: string | null
  isRoot: boolean
  onDelete: (id: string) => Promise<void>
  onResolve: (id: string) => Promise<void>
}) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const isAuthor = currentUserId === comment.user_id

  return (
    <div className={isRoot ? 'comment comment-root' : 'comment comment-reply'}>
      <div className="comment-header">
        <span className="comment-author">
          {comment.author_username ?? 'unknown'}
        </span>
        <span className="comment-time">
          {new Date(comment.created_at).toLocaleString()}
        </span>
        {comment.resolved && (
          <span className="comment-resolved-badge">resolved</span>
        )}
        {isRoot && comment.file_path && (
          <span className="comment-anchor">
            {comment.file_path}
            {comment.line_number != null && `:${comment.line_number}`}
          </span>
        )}
      </div>
      <div className="comment-body">{comment.body}</div>
      <div className="comment-actions">
        {isRoot && (
          <button
            className="comment-action"
            onClick={() => onResolve(comment.id)}
          >
            {comment.resolved ? 'Unresolve' : 'Resolve'}
          </button>
        )}
        {isAuthor && (
          <button
            className="comment-action"
            onClick={() => {
              if (confirmDelete) {
                onDelete(comment.id)
              } else {
                setConfirmDelete(true)
              }
            }}
          >
            {confirmDelete ? 'Confirm?' : 'Delete'}
          </button>
        )}
      </div>
    </div>
  )
}

export default function CommentThread({
  thread,
  currentUserId,
  onReply,
  onDelete,
  onResolve,
}: Props) {
  const [replying, setReplying] = useState(false)
  const [replyBody, setReplyBody] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submitReply = async () => {
    if (!replyBody.trim()) return
    setSubmitting(true)
    try {
      await onReply(thread.root.id, replyBody.trim())
      setReplyBody('')
      setReplying(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="comment-thread">
      <CommentBody
        comment={thread.root}
        currentUserId={currentUserId}
        isRoot
        onDelete={onDelete}
        onResolve={onResolve}
      />
      {thread.replies.length > 0 && (
        <div className="comment-replies">
          {thread.replies.map((reply) => (
            <CommentBody
              key={reply.id}
              comment={reply}
              currentUserId={currentUserId}
              isRoot={false}
              onDelete={onDelete}
              onResolve={onResolve}
            />
          ))}
        </div>
      )}
      <div className="comment-reply-form">
        {replying ? (
          <>
            <textarea
              value={replyBody}
              onChange={(e) => setReplyBody(e.target.value)}
              placeholder="Reply..."
              rows={2}
              autoFocus
            />
            <div className="comment-form-actions">
              <button
                className="btn-primary btn-sm"
                onClick={submitReply}
                disabled={submitting || !replyBody.trim()}
              >
                Reply
              </button>
              <button
                className="btn-secondary btn-sm"
                onClick={() => setReplying(false)}
              >
                Cancel
              </button>
            </div>
          </>
        ) : (
          <button className="comment-action" onClick={() => setReplying(true)}>
            Reply
          </button>
        )}
      </div>
    </div>
  )
}
