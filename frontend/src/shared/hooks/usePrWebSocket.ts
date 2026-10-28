import { useEffect, useRef } from 'react'
import { useAuthStore } from '../useAuthStore'

export interface WsMessage {
  type: string
  payload: unknown
}

function buildWsUrl(prId: string, token: string): string {
  const apiBase = import.meta.env.VITE_API_URL as string | undefined
  if (apiBase) {
    // e.g. "http://212.57.127.83/api" or "/api" -> ws equivalent
    const url = new URL(apiBase, window.location.origin)
    const proto = url.protocol === 'https:' ? 'wss' : 'ws'
    return `${proto}://${url.host}${url.pathname.replace(/\/$/, '')}/ws/prs/${prId}?token=${encodeURIComponent(token)}`
  }
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/ws/prs/${prId}?token=${encodeURIComponent(token)}`
}

export function usePrWebSocket(
  prId: string | null,
  onMessage: (message: WsMessage) => void,
): void {
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const accessToken = useAuthStore((s) => s.accessToken)

  useEffect(() => {
    if (!prId || !accessToken) return

    let closedByUs = false
    let retryDelay = 1000
    let socket: WebSocket | null = null
    let retryTimer: ReturnType<typeof setTimeout> | null = null

    const connect = () => {
      socket = new WebSocket(buildWsUrl(prId, accessToken))

      socket.onopen = () => {
        retryDelay = 1000
      }

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data as string) as WsMessage
          onMessageRef.current(message)
        } catch {
          // ignore malformed frames
        }
      }

      socket.onclose = () => {
        if (closedByUs) return
        retryTimer = setTimeout(connect, retryDelay)
        retryDelay = Math.min(retryDelay * 2, 30_000)
      }
    }

    connect()

    return () => {
      closedByUs = true
      if (retryTimer) clearTimeout(retryTimer)
      if (socket) {
        socket.onclose = null
        socket.close()
      }
    }
  }, [prId, accessToken])
}
