import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8001'

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

export const login = async (username: string, password: string) => {
  const res = await api.post('/auth/login', { username, password })
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

export default api
