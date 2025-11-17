import axios from 'axios'

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const rawPrefix = import.meta.env.VITE_API_PREFIX ?? '/api'

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '')
const normalizePrefix = (prefix: string) => {
  if (!prefix) return ''
  const stripped = prefix.replace(/^\/+|\/+$/g, '')
  return stripped ? `/${stripped}` : ''
}
const ensureLeadingSlash = (value: string) => (value.startsWith('/') ? value : `/${value}`)

export const API_BASE_URL = trimTrailingSlash(rawBaseUrl)
export const API_PREFIX = normalizePrefix(rawPrefix)

export const withApiPrefix = (path: string) => {
  const cleanedPath = ensureLeadingSlash(path)
  return API_PREFIX ? `${API_PREFIX}${cleanedPath}` : cleanedPath
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      console.error('API error', {
        url: error.config?.url,
        method: error.config?.method,
        message: error.message,
        status: error.response?.status,
      })
    }
    return Promise.reject(error)
  }
)

export interface Candle {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  symbol?: string
}

export interface CandlesResponse {
  symbol: string
  interval: string
  count: number
  data: Candle[]
}

export const fetchCandles = async (
  symbol: string,
  interval: string = '1d',
  limit: number = 100
): Promise<CandlesResponse> => {
  const response = await api.get<{ symbol: string; interval: string; data: Candle[] }>(
    withApiPrefix(`/candles/${symbol}`),
    { params: { interval, limit } }
  )
  const enrichedData = response.data.data.map(candle => ({ ...candle, symbol }))
  return {
    symbol: response.data.symbol,
    interval: response.data.interval,
    data: enrichedData,
    count: enrichedData.length,
  }
}

export const fetchSymbols = async (): Promise<string[]> => {
  const response = await api.get<{ symbols: string[] }>(withApiPrefix('/symbols'))
  return response.data.symbols
}

export const checkHealth = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await api.get<{ status: string; timestamp: string }>('/health')
  return response.data
}

export const checkReadiness = async (): Promise<{ status: string; timestamp: string }> => {
  try {
    const response = await api.get<{ status: string; timestamp: string }>('/ready')
    return response.data
  } catch {
    return checkHealth()
  }
}

// AI endpoints
export interface AIAnalysisResponse {
  symbol: string
  analysis: string
  timestamp: string
}

export interface PortfolioAdviceResponse {
  advice: string
  timestamp: string
}

export const analyzeMarket = async (symbol: string, marketData: any): Promise<AIAnalysisResponse> => {
  const response = await api.post<AIAnalysisResponse>(
    withApiPrefix('/ai/query'),
    {
      user_id: 'dashboard',
      question: `Provide an analysis for ${symbol} with context ${JSON.stringify(marketData)}`,
    }
  )
  return response.data
}

export const getPortfolioAdvice = async (portfolioData: any): Promise<PortfolioAdviceResponse> => {
  const response = await api.post<PortfolioAdviceResponse>(
    withApiPrefix('/ai/query'),
    {
      user_id: 'portfolio',
      question: `Portfolio guidance for data: ${JSON.stringify(portfolioData)}`,
    }
  )
  return response.data as unknown as PortfolioAdviceResponse
}

export const processAIPrompt = async (prompt: string, context?: any): Promise<{ response: string }> => {
  const response = await api.post<{ content: string }>(
    withApiPrefix('/ai/query'),
    {
      user_id: 'assistant',
      question: `${prompt}\nContext: ${JSON.stringify(context || {})}`,
    }
  )
  return { response: response.data.content }
}

// Portfolio endpoints
export interface PortfolioData {
  total_value: number
  cash: number
  positions_value: number
  pnl: number
  positions?: Position[]
}

export interface Position {
  symbol: string
  quantity: number
  avg_price: number
  current_price: number
  value: number
  pnl: number
  pnl_percent: number
}

export const fetchPortfolio = async (): Promise<PortfolioData> => {
  const token = localStorage.getItem('access_token')
  const response = await api.get<PortfolioData>('/portfolio', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const fetchPositions = async (): Promise<Position[]> => {
  const token = localStorage.getItem('access_token')
  const response = await api.get<Position[]>('/positions', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

// News endpoints
export interface NewsItem {
  id: string
  title: string
  summary: string
  source: string
  published_at: string
  url?: string
  sentiment?: 'positive' | 'negative' | 'neutral'
  symbols?: string[]
}

export const fetchNews = async (): Promise<NewsItem[]> => {
  const token = localStorage.getItem('access_token')
  try {
    const response = await api.get<{ articles?: NewsItem[], data?: NewsItem[] }>('/news', {
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = response.data.articles ?? response.data.data
    return data ?? []
  } catch (error) {
    // Return empty array if endpoint doesn't exist
    return []
  }
}

// Paper Trading endpoints
export interface PaperOrderRequest {
  symbol: string
  side: string
  quantity: number
  order_type?: string
  price?: number
  stop_price?: number
  current_market_price?: number
}

export interface PaperOrderResponse {
  order_id: string
  symbol: string
  side: string
  quantity: number
  order_type: string
  status: string
  filled_quantity: number
  avg_fill_price: number
  fill_price?: number
  created_at: string
  filled_at?: string
}

export const placePaperOrder = async (order: PaperOrderRequest): Promise<PaperOrderResponse> => {
  const token = localStorage.getItem('access_token')
  const response = await api.post<PaperOrderResponse>('/paper-trading/place-order', order, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const getPaperPortfolio = async (): Promise<any> => {
  const token = localStorage.getItem('access_token')
  const response = await api.get('/paper-trading/portfolio', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const getPaperPositions = async (): Promise<any> => {
  const token = localStorage.getItem('access_token')
  const response = await api.get('/paper-trading/positions', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const getPaperOrders = async (limit: number = 50): Promise<any> => {
  const token = localStorage.getItem('access_token')
  const response = await api.get(`/paper-trading/orders?limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const resetPaperPortfolio = async (initialCash: number = 100000): Promise<any> => {
  const token = localStorage.getItem('access_token')
  const response = await api.post('/paper-trading/reset', { initial_cash: initialCash }, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export default api
