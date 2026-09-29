import api from './client'
import type { User } from '../useAuthStore'

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export async function refresh(): Promise<string> {
  const { data } = await api.post<{ access_token: string }>('/auth/refresh')
  return data.access_token
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

export function login(): void {
  window.location.href = `${import.meta.env.VITE_API_URL || '/api'}/auth/github/login`
}
