import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000'

type TradePayload = {
  symbol: string
  qty: number
  side: 'buy' | 'sell'
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
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  const res = await api.post('/auth/login', formData)
  return res.data
}

export const getPortfolio = async () => (await api.get('/portfolio')).data
export const getPrice = async (symbol: string) => (await api.get(`/price/${symbol}`)).data
export const placeTrade = async (trade: TradePayload) => (await api.post('/trades', trade)).data

export default api
