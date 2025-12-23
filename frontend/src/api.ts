import axios from 'axios'

const API_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

type TradePayload = {
  symbol: string
  qty: number
  side: 'buy' | 'sell'
}

export type IndicatorsResponse = {
  timestamp: string[]
  price: number[]
  indicators: Record<string, Array<number | null>>
}

export type PositionSnapshot = {
  symbol: string
  direction: 'long' | 'short' | 'flat'
  qty: number
  entry_price: number
  mark_price: number
  status: 'open' | 'closed'
  last_updated: string
}

export type RegimeHistoryPoint = {
  timestamp: string
  label: string
  probability: number
  volatility: number
}

export type RegimeAnalytics = {
  symbol: string
  current_regime: string
  probability: number
  realized_volatility: number
  atr: number
  window: number
  updated_at: string
  history: RegimeHistoryPoint[]
}

export type OrderBookLevel = {
  price: number
  size: number
}

export type OrderBookHistoryPoint = {
  timestamp: string
  imbalance: number
  state: string
}

export type OrderBookAnalytics = {
  symbol: string
  timestamp: string
  imbalance: number
  state: string
  spread: number
  buy_pressure: number
  sell_pressure: number
  best_bid?: number
  best_ask?: number
  bids: OrderBookLevel[]
  asks: OrderBookLevel[]
  history: OrderBookHistoryPoint[]
}

const api = axios.create({
  baseURL: API_URL,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

type LoginPayload = {
  username: string
  password: string
}

export const login = async (identifier: string, password: string) => {
  const normalized = identifier.trim()
  if (!normalized) {
    throw new Error('Email or username is required')
  }

  const payload: LoginPayload = {
    // Backend expects the identifier under the `username` key even if it is an email.
    username: normalized,
    password,
  }

  const res = await api.post(
    '/auth/login',
    payload,
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )
  return res.data
}

export const getPortfolio = async () => (await api.get('/portfolio')).data
export const getPrice = async (symbol: string) => (await api.get(`/price/${symbol}`)).data
export const placeTrade = async (trade: TradePayload) => (await api.post('/trades', trade)).data
export const getIndicators = async (symbol: string): Promise<IndicatorsResponse> =>
  (await api.get(`/indicators/${symbol}`)).data
export const getPositions = async (): Promise<PositionSnapshot[]> => (await api.get('/positions')).data
export const getRegimeAnalytics = async (symbol: string): Promise<RegimeAnalytics> =>
  (await api.get(`/analytics/regime/${symbol}`)).data
export const getOrderBookAnalytics = async (symbol: string): Promise<OrderBookAnalytics> =>
  (await api.get(`/analytics/order-book/${symbol}`)).data

export type Order = {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  qty: number
  price?: number
  status: 'pending' | 'filled' | 'cancelled'
  created_at: string
  filled_at?: string
}

export type PnLData = {
  day_pnl: number
  total_pnl: number
  unrealized_pnl: number
  realized_pnl: number
}

export type LogEntry = {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  source: string
}

export const getOrders = async (): Promise<Order[]> => (await api.get('/portfolio/orders')).data
export const getPnL = async (): Promise<PnLData> => (await api.get('/portfolio/pnl')).data
export const getTrades = async (): Promise<any[]> => (await api.get('/portfolio/trades')).data
export const getLogs = async (): Promise<LogEntry[]> => (await api.get('/logs')).data

export const cancelOrder = async (orderId: number) => (await api.post('/trade/cancel_order', { order_id: orderId })).data
export const modifyOrder = async (orderId: number, qty?: number, price?: number) => (await api.post('/trade/modify_order', { order_id: orderId, qty, price })).data
export const startEngine = async () => (await api.post('/engine/start')).data
export const stopEngine = async () => (await api.post('/engine/stop')).data

export default api
