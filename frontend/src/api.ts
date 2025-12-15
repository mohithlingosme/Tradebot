import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000'

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

export default api
