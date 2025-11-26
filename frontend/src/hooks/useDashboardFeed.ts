import { useCallback, useEffect, useMemo, useState } from 'react'
import { API_BASE_URL, fetchLogs, fetchOrders, fetchPnl, fetchPositions, fetchRiskStatus, fetchStrategyStatus, LogEntry, OrderRow, PnLStatus, Position, RiskStatus, StrategyStatus, withApiPrefix } from '../services/api'
import { useWebSocket } from './useWebSocket'

interface DashboardFeed {
  pnl: PnLStatus
  positions: Position[]
  orders: OrderRow[]
  logs: LogEntry[]
  strategy: StrategyStatus
  risk: RiskStatus
  isLive: boolean
}

const defaultFeed: DashboardFeed = {
  pnl: { total: 0, realized: 0, unrealized: 0 },
  positions: [],
  orders: [],
  logs: [],
  strategy: { name: 'Unknown', state: 'STOPPED' },
  risk: { max_daily_loss_pct: 0.05, used_pct: 0, circuit_breaker: false },
  isLive: false,
}

type WsMessage =
  | { type: 'pnl'; total: number; realized?: number; unrealized?: number }
  | { type: 'order'; order: OrderRow }
  | { type: 'position'; positions: Position[] }
  | { type: 'log'; log: LogEntry }
  | { type: 'strategy'; strategy: StrategyStatus }
  | { type: 'risk'; risk: RiskStatus }
  | Record<string, any>

export const buildDashboardWsUrl = () => {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL as string
  try {
    const base = new URL(API_BASE_URL)
    const wsProtocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsProtocol}//${base.host}${withApiPrefix('/ws/dashboard')}`
  } catch {
    return 'ws://localhost:8000/ws/dashboard'
  }
}

export const useDashboardFeed = (): DashboardFeed => {
  const [feed, setFeed] = useState<DashboardFeed>(defaultFeed)
  const wsUrl = useMemo(buildDashboardWsUrl, [])

  useEffect(() => {
    const loadInitial = async () => {
      const [pnl, positions, orders, logs, strategy, risk] = await Promise.all([
        fetchPnl(),
        fetchPositions().catch(() => []),
        fetchOrders().catch(() => []),
        fetchLogs().catch(() => []),
        fetchStrategyStatus(),
        fetchRiskStatus(),
      ])
      setFeed((prev) => ({
        ...prev,
        pnl,
        positions,
        orders,
        logs,
        strategy,
        risk,
      }))
    }
    loadInitial()
  }, [])

  const handleOpen = useCallback(() => setFeed((prev) => ({ ...prev, isLive: true })), [])
  const handleClose = useCallback(() => setFeed((prev) => ({ ...prev, isLive: false })), [])
  const handleMessage = useCallback((message: WsMessage) => {
    setFeed((prev) => {
      switch (message.type) {
        case 'pnl':
          return { ...prev, pnl: { total: message.total, realized: message.realized ?? prev.pnl.realized, unrealized: message.unrealized ?? prev.pnl.unrealized } }
        case 'order': {
          const updated = [message.order, ...prev.orders].slice(0, 50)
          return { ...prev, orders: updated }
        }
        case 'position':
          return { ...prev, positions: message.positions }
        case 'log': {
          const updatedLogs = [message.log, ...prev.logs].slice(0, 200)
          return { ...prev, logs: updatedLogs }
        }
        case 'strategy':
          return { ...prev, strategy: message.strategy }
        case 'risk':
          return { ...prev, risk: message.risk }
        default:
          return prev
      }
    })
  }, [])

  useWebSocket({
    url: wsUrl,
    onOpen: handleOpen,
    onClose: handleClose,
    onMessage: handleMessage,
  })

  return feed
}
