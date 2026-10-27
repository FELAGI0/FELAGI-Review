import { type ReactNode } from 'react'
import { AuthProvider } from './AuthProvider'

export function AppLayout({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}
