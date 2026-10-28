import type { DiffFile } from '../../shared/api/repos'
import DiffFileView from './DiffFileView'

interface Props {
  file: DiffFile
}

export default function DiffViewer({ file }: Props) {
  return <DiffFileView file={file} comments={[]} onInlineSubmit={async () => {}} />
}
