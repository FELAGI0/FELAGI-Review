import { useMemo, useState } from 'react'
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued'
import type { DiffFile } from '../../shared/api/repos'
import type { Comment } from '../../shared/api/comments'
import InlineCommentForm from '../comments/InlineCommentForm'
import { darkStyles, fileToSides } from './diffStyles'

interface Props {
  file: DiffFile
  comments: Comment[]
  onInlineSubmit: (
    body: string,
    filePath: string,
    lineNumber: number,
  ) => Promise<void>
}

export default function DiffFileView({ file, comments, onInlineSubmit }: Props) {
  const { oldCode, newCode } = useMemo(() => fileToSides(file), [file])
  const [activeLine, setActiveLine] = useState<number | null>(null)

  const fileComments = comments.filter((c) => c.file_path === file.path)
  const commentsByLine = new Map<number, Comment[]>()
  for (const comment of fileComments) {
    if (comment.line_number != null) {
      const list = commentsByLine.get(comment.line_number) ?? []
      list.push(comment)
      commentsByLine.set(comment.line_number, list)
    }
  }
  const commentedLines = [...commentsByLine.keys()]

  const lineHasComment = (lineNumber: number) =>
    commentsByLine.has(lineNumber)

  return (
    <div className="diff-file">
      <div className="diff-file-header">
        <span className="diff-file-path">{file.path}</span>
        <span className="diff-file-stats">
          <span className="diff-add">+{file.additions}</span>{' '}
          <span className="diff-del">-{file.deletions}</span>
          {file.status !== 'modified' && (
            <span className="diff-file-status">{file.status}</span>
          )}
          {fileComments.length > 0 && (
            <span className="diff-file-comments">{fileComments.length} comments</span>
          )}
        </span>
      </div>

      {file.is_binary ? (
        <div className="diff-binary">Binary file not displayed</div>
      ) : (
        <ReactDiffViewer
          oldValue={oldCode}
          newValue={newCode}
          splitView={false}
          useDarkTheme
          styles={darkStyles}
          compareMethod={DiffMethod.WORDS}
          renderGutter={(gutterProps) => {
            const lineNumber = gutterProps.lineNumber ?? 0
            // DiffType enum: DEFAULT = 0, ADDED = 1, REMOVED = 2, CHANGED = 3
            // commentable: added lines (new side) and unchanged context
            const canComment =
              gutterProps.type === 1 || gutterProps.type === 0
            const hasComment = lineNumber !== 0 && lineHasComment(lineNumber)
            return (
              <div className="diff-gutter-cell">
                <span className="diff-gutter-num">
                  {lineNumber === 0 ? '' : lineNumber}
                </span>
                {canComment && lineNumber !== 0 && (
                  hasComment ? (
                    <span
                      className="diff-gutter-marker commented"
                      title={`${commentsByLine.get(lineNumber)!.length} comment(s)`}
                    >
                      ●
                    </span>
                  ) : (
                    <button
                      className="diff-gutter-add"
                      title="Comment on this line"
                      onClick={() => setActiveLine(lineNumber)}
                    >
                      +
                    </button>
                  )
                )}
              </div>
            )
          }}
        />
      )}

      {activeLine != null && (
        <InlineCommentForm
          filePath={file.path}
          lineNumber={activeLine}
          onClose={() => setActiveLine(null)}
          onSubmit={async (body) => {
            await onInlineSubmit(body, file.path, activeLine)
            setActiveLine(null)
          }}
        />
      )}

      {commentedLines.length > 0 && (
        <div className="diff-inline-comments">
          {commentedLines.map((line) => (
            <div key={line} className="diff-line-comments">
              <div className="diff-line-comments-header">
                Line {line} - {commentsByLine.get(line)!.length} comment(s)
              </div>
              {commentsByLine.get(line)!.map((comment) => (
                <div key={comment.id} className="inline-comment-item">
                  <span className="comment-author">
                    {comment.author_username ?? 'unknown'}
                  </span>
                  <span className="comment-body">{comment.body}</span>
                  {comment.resolved && (
                    <span className="comment-resolved-badge">resolved</span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
