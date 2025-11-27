import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  API_BASE_URL,
  fetchLogs,
  fetchOrders,
  fetchPnl,
  fetchPositions,
  fetchRiskStatus,
  fetchStrategyStatus,
  LogEntry,
  OrderRow,
  PnLStatus,
  Position,
  RiskStatus,
  StrategyStatus,
  withApiPrefix,
} from '../services/api'
import { useWebSocket } from './useWebSocket'

interface DashboardFeedState {
  pnl: PnLStatus
  positions: Position[]
  orders: OrderRow[]
  logs: LogEntry[]
  strategy: StrategyStatus
  risk: RiskStatus
  isLive: boolean
  lastUpdated?: string
}

interface DashboardFeed extends DashboardFeedState {
  isRefreshing: boolean
  refreshSnapshot: () => Promise<void>
}

const defaultFeed: DashboardFeedState = {
  pnl: { total: 0, realized: 0, unrealized: 0 },
  positions: [],
  orders: [],
  logs: [],
  strategy: { name: 'Unknown', state: 'STOPPED' },
  risk: { max_daily_loss_pct: 0.05, used_pct: 0, circuit_breaker: false },
  isLive: false,
  lastUpdated: undefined,
}

type WsMessage =
  | { type: 'pnl'; total: number; realized?: number; unrealized?: number }
  | { type: 'order'; order: OrderRow }
  | { type: 'position'; positions: Position[] }
  | { type: 'log'; log: LogEntry }
  | { type: 'strategy'; strategy: StrategyStatus }
  | { type: 'risk'; risk: RiskStatus }
  | { type: 'snapshot'; pnl: PnLStatus; positions: Position[]; orders: OrderRow[]; logs: LogEntry[]; strategy: StrategyStatus; risk: RiskStatus }

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
  const [feed, setFeed] = useState<DashboardFeedState>(defaultFeed)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const wsUrl = useMemo(buildDashboardWsUrl, [])

  const refreshSnapshot = useCallback(async () => {
    setIsRefreshing(true)
    try {
      const [pnl, positions, orders, logs, strategy, risk] = await Promise.all([
        fetchPnl().catch(() => defaultFeed.pnl),
        fetchPositions().catch(() => defaultFeed.positions),
        fetchOrders().catch(() => defaultFeed.orders),
        fetchLogs().catch(() => defaultFeed.logs),
        fetchStrategyStatus().catch(() => defaultFeed.strategy),
        fetchRiskStatus().catch(() => defaultFeed.risk),
      ])
      setFeed((prev) => ({
        ...prev,
        pnl,
        positions,
        orders,
        logs,
        strategy,
        risk,
        lastUpdated: new Date().toISOString(),
      }))
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    refreshSnapshot()
  }, [refreshSnapshot])

  const handleOpen = useCallback(() => setFeed((prev) => ({ ...prev, isLive: true })), [])
  const handleClose = useCallback(() => setFeed((prev) => ({ ...prev, isLive: false })), [])
  const handleError = useCallback(() => setFeed((prev) => ({ ...prev, isLive: false })), [])
  const handleMessage = useCallback((message: any) => {
    const payload = message as WsMessage
    setFeed((prev) => {
      const lastUpdated = new Date().toISOString()
      switch (payload.type) {
        case 'pnl':
          return {
            ...prev,
            pnl: {
              total: payload.total,
              realized: payload.realized ?? prev.pnl.realized,
              unrealized: payload.unrealized ?? prev.pnl.unrealized,
            },
            lastUpdated,
          }
        case 'order': {
          const updated = [payload.order, ...prev.orders].slice(0, 50)
          return { ...prev, orders: updated, lastUpdated }
        }
        case 'position':
          return { ...prev, positions: payload.positions, lastUpdated }
        case 'log': {
          const updatedLogs = [payload.log, ...prev.logs].slice(0, 200)
          return { ...prev, logs: updatedLogs, lastUpdated }
        }
        case 'strategy':
          return { ...prev, strategy: payload.strategy, lastUpdated }
        case 'risk':
          return { ...prev, risk: payload.risk, lastUpdated }
        case 'snapshot':
          return {
            ...prev,
            pnl: payload.pnl,
            positions: payload.positions,
            orders: payload.orders,
            logs: payload.logs,
            strategy: payload.strategy,
            risk: payload.risk,
            isLive: true,
            lastUpdated,
          }
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
    onError: handleError,
    reconnect: true,
    reconnectIntervalMs: 5000,
    maxReconnectAttempts: 50,
  })

  const isLive = feed.isLive

  useEffect(() => {
    if (isLive) return
    const id = window.setInterval(() => {
      refreshSnapshot().catch(() => {
        /* best-effort */
      })
    }, 15000)
    return () => clearInterval(id)
  }, [isLive, refreshSnapshot])

  return { ...feed, isRefreshing, refreshSnapshot }
}
