import { useState } from 'react'

interface Props {
  filePath: string
  lineNumber: number
  onClose: () => void
  onSubmit: (body: string) => Promise<void>
}

export default function InlineCommentForm({
  filePath,
  lineNumber,
  onClose,
  onSubmit,
}: Props) {
  const [body, setBody] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    if (!body.trim()) return
    setSubmitting(true)
    try {
      await onSubmit(body.trim())
      setBody('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="inline-comment-form">
      <div className="inline-comment-anchor">
        Comment on {filePath.split('/').pop()}:{lineNumber}
      </div>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Leave a comment..."
        rows={3}
        autoFocus
        onKeyDown={(e) => {
          if (e.key === 'Escape') onClose()
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submit()
        }}
      />
      <div className="comment-form-actions">
        <button
          className="btn-primary btn-sm"
          onClick={submit}
          disabled={submitting || !body.trim()}
        >
          {submitting ? 'Sending...' : 'Comment'}
        </button>
        <button className="btn-secondary btn-sm" onClick={onClose}>
          Cancel
        </button>
      </div>
    </div>
  )
}
