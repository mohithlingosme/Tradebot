import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchCandles, fetchSymbols } from '../services/api'
import { useWebSocket } from './useWebSocket'

interface MarketData {
  [symbol: string]: {
    price: number
    change: number
    changePercent: number
    timestamp: string
    volume: number
  }
}

export function useMarketData(selectedSymbol: string, interval: string) {
  const [marketData, setMarketData] = useState<MarketData>({})

  // Fetch historical data
  const { data: candlesData, isLoading: candlesLoading } = useQuery({
    queryKey: ['candles', selectedSymbol, interval],
    queryFn: () => fetchCandles(selectedSymbol, interval, 100),
    enabled: !!selectedSymbol,
    refetchInterval: 60000, // Refetch every minute
  })

  // WebSocket for real-time updates
  const wsUrl =
    import.meta.env.VITE_WS_URL ||
    `${(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace('http', 'ws')}/ws`

  const { isConnected, subscribe } = useWebSocket({
    url: wsUrl,
    onMessage: (message) => {
      if (message.type === 'price_update') {
        setMarketData(prev => ({
          ...prev,
          [message.symbol]: {
            price: message.price,
            change: message.change,
            changePercent: message.change_percent,
            timestamp: message.timestamp,
            volume: message.volume
          }
        }))
      }
    }
  })

  // Subscribe to real-time updates when symbol changes
  useEffect(() => {
    if (isConnected && selectedSymbol) {
      subscribe([selectedSymbol])
    }
  }, [isConnected, selectedSymbol, subscribe])

  return {
    candlesData,
    marketData,
    isLoading: candlesLoading,
    isConnected
  }
}

export function useSymbols() {
  return useQuery({
    queryKey: ['symbols'],
    queryFn: fetchSymbols,
  })
}
