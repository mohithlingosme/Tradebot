import { useQuery } from '@tanstack/react-query'
import { fetchCandles } from '../services/api'

interface WatchlistItemProps {
  symbol: string
  price?: number
  onRemove: (symbol: string) => void
}

function WatchlistItem({ symbol, price: propPrice, onRemove }: WatchlistItemProps) {
  const { data: candles, isLoading, error } = useQuery({
    queryKey: ['candles', symbol, '1d', 1],
    queryFn: () => fetchCandles(symbol, '1d', 1),
    refetchInterval: 30000, // Refetch every 30 seconds
    enabled: !propPrice, // Only fetch if price not provided
  })

  const latestCandle = candles?.data?.[0]
  const price = propPrice || latestCandle?.close || 0
  const openPrice = latestCandle?.open || price
  const change = price - openPrice
  const changePercent = openPrice > 0 ? (change / openPrice) * 100 : 0

  return (
    <div className={`watchlist-item ${change >= 0 ? 'positive' : 'negative'}`}>
      <div className="symbol-info">
        <span className="symbol">{symbol}</span>
        <span className="price">${price.toFixed(2)}</span>
      </div>

      <div className="change-info">
        <span className="change">${change.toFixed(2)}</span>
        <span className="change-percent">({changePercent.toFixed(2)}%)</span>
      </div>

      <button className="remove-btn" onClick={() => onRemove(symbol)}>×</button>

      {isLoading && <div className="loading">Loading...</div>}
      {error && <div className="error">Error loading data</div>}
    </div>
  )
}

export default WatchlistItem
