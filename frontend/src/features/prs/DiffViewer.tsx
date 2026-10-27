import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued'
import type { DiffFile } from '../../shared/api/repos'

interface Props {
  file: DiffFile
}

const darkStyles = {
  variables: {
    dark: {
      diffViewerBackground: '#111827',
      diffViewerColor: '#F9FAFB',
      additionBackground: '#0d3320',
      additionColor: '#6ee7a0',
      deletionBackground: '#3d1418',
      deletionColor: '#f28b92',
      wordAdditionBackground: '#1a5c38',
      wordDeletionBackground: '#62171d',
      emptyLineBackground: '#0B0F19',
      gutterBackground: '#0B0F19',
      gutterBackgroundDark: '#0B0F19',
      highlightBackground: '#1c2333',
      highlightGutterBackground: '#151b2b',
      codeFoldGutterBackground: '#0B0F19',
      codeFoldBackground: '#10161f',
      fontFace: 'Roboto Mono, Consolas, monospace',
    },
  },
  line: { padding: '2px 10px' },
}

export default function DiffViewer({ file }: Props) {
  const { oldCode, newCode } = fileToSides(file)

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
          {file.is_binary && <span className="diff-file-status">binary</span>}
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
          hideLineNumbers={false}
        />
      )}
    </div>
  )
}

function fileToSides(file: DiffFile): { oldCode: string; newCode: string } {
  const oldLines: string[] = []
  const newLines: string[] = []
  for (const hunk of file.hunks) {
    for (const line of hunk.lines) {
      switch (line.type) {
        case 'add':
          oldLines.push('')
          newLines.push(line.content)
          break
        case 'del':
          oldLines.push(line.content)
          newLines.push('')
          break
        case 'context':
          oldLines.push(line.content)
          newLines.push(line.content)
          break
        case 'meta':
          oldLines.push('')
          newLines.push('')
          break
      }
    }
  }
  return { oldCode: oldLines.join('\n'), newCode: newLines.join('\n') }
}
