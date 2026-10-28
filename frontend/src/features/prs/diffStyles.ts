import type { DiffFile } from '../../shared/api/repos'

export const darkStyles = {
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

export function fileToSides(file: DiffFile): { oldCode: string; newCode: string } {
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
