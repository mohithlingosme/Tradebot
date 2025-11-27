import { useEffect, useRef, useState } from 'react'

interface WebSocketMessage {
  type: string
  [key: string]: any
}

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: (event?: CloseEvent) => void
  onError?: (error: Event) => void
  reconnect?: boolean
  reconnectIntervalMs?: number
  maxReconnectAttempts?: number
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  onError,
  reconnect = true,
  reconnectIntervalMs = 4000,
  maxReconnectAttempts = 10,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const cleanup = () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
      if (wsRef.current) {
        wsRef.current.onopen = null
        wsRef.current.onmessage = null
        wsRef.current.onclose = null
        wsRef.current.onerror = null
        wsRef.current.close()
      }
    }

    const connect = () => {
      cleanup()
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttempts.current = 0
        setIsConnected(true)
        onOpen?.()
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        onClose?.(event)
        if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1
          reconnectTimer.current = setTimeout(connect, reconnectIntervalMs)
        }
      }

      ws.onerror = (error) => {
        onError?.(error)
      }
    }

    connect()
    return cleanup
  }, [url, onMessage, onOpen, onClose, onError, reconnect, reconnectIntervalMs, maxReconnectAttempts])

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }

  const subscribe = (symbols: string[]) => {
    sendMessage({
      type: 'subscribe',
      symbols
    })
  }

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe
  }
}
