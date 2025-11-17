import { useState, useEffect } from 'react'
import axios from 'axios'
import SymbolSelector from '../components/SymbolSelector'
import { useMarketData } from '../hooks/useMarketData'
import '../styles/PaperTrading.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Portfolio {
  cash: number
  positions_value: number
  total_value: number
  unrealized_pnl: number
  realized_pnl: number
  total_pnl: number
  initial_cash: number
  return_percent: number
}

interface Position {
  symbol: string
  quantity: number
  average_entry_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
  total_pnl: number
  market_value: number
}

interface Order {
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
}

export default function PaperTrading() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  
  // Order form state
  const [symbol, setSymbol] = useState('')
  const [side, setSide] = useState<'buy' | 'sell'>('buy')
  const [quantity, setQuantity] = useState<number>(1)
  const [orderType, setOrderType] = useState<'market' | 'limit' | 'stop'>('market')
  const [price, setPrice] = useState<number>(0)
  const [placingOrder, setPlacingOrder] = useState(false)
  
  const { marketData } = useMarketData(symbol, '1d')

  useEffect(() => {
    fetchPortfolio()
    fetchPositions()
    fetchOrders()
    
    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      fetchPortfolio()
      fetchPositions()
      if (symbol && marketData[symbol]?.price) {
        updatePrices({ [symbol]: marketData[symbol].price })
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (symbol && marketData[symbol]?.price && price === 0) {
      setPrice(marketData[symbol].price)
    }
  }, [symbol, marketData])

  const fetchPortfolio = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/paper-trading/portfolio`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setPortfolio(response.data)
    } catch (error) {
      console.error('Error fetching portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchPositions = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/paper-trading/positions`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setPositions(response.data.positions || [])
    } catch (error) {
      console.error('Error fetching positions:', error)
    }
  }

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/paper-trading/orders?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setOrders(response.data.orders || [])
    } catch (error) {
      console.error('Error fetching orders:', error)
    }
  }

  const updatePrices = async (priceUpdates: Record<string, number>) => {
    try {
      const token = localStorage.getItem('access_token')
      await axios.post(`${API_BASE_URL}/paper-trading/update-prices`, priceUpdates, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchPortfolio()
      fetchPositions()
    } catch (error) {
      console.error('Error updating prices:', error)
    }
  }

  const placeOrder = async () => {
    if (!symbol || quantity <= 0) {
      alert('Please select a symbol and enter a valid quantity')
      return
    }

    if (orderType === 'limit' && price <= 0) {
      alert('Please enter a valid price for limit orders')
      return
    }

    setPlacingOrder(true)

    try {
      const token = localStorage.getItem('access_token')
      const currentPrice = marketData[symbol]?.price || price
      
      await axios.post(
        `${API_BASE_URL}/paper-trading/place-order`,
        {
          symbol,
          side,
          quantity,
          order_type: orderType,
          price: orderType === 'limit' ? price : undefined,
          stop_price: orderType === 'stop' ? price : undefined,
          current_market_price: orderType === 'market' ? currentPrice : undefined,
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      // Refresh data
      fetchPortfolio()
      fetchPositions()
      fetchOrders()

      // Reset form
      setQuantity(1)
      setPrice(marketData[symbol]?.price || 0)
      
      alert('Order placed successfully!')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to place order')
    } finally {
      setPlacingOrder(false)
    }
  }

  const resetPortfolio = async () => {
    if (!confirm('Are you sure you want to reset your paper trading portfolio? This cannot be undone.')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      await axios.post(
        `${API_BASE_URL}/paper-trading/reset`,
        { initial_cash: 100000 },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      
      fetchPortfolio()
      fetchPositions()
      fetchOrders()
      alert('Portfolio reset successfully!')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to reset portfolio')
    }
  }

  const currentPrice = symbol && marketData[symbol]?.price ? marketData[symbol].price : 0

  if (loading) {
    return <div className="loading">Loading paper trading...</div>
  }

  return (
    <div className="paper-trading">
      <div className="paper-trading-header">
        <div>
          <h1>Paper Trading</h1>
          <p className="subtitle">Practice trading with virtual money</p>
        </div>
        <button onClick={resetPortfolio} className="reset-button">
          Reset Portfolio
        </button>
      </div>

      {/* Portfolio Summary */}
      {portfolio && (
        <div className="portfolio-summary-section">
          <h2>Portfolio Summary</h2>
          <div className="portfolio-metrics">
            <div className="metric-card">
              <div className="metric-label">Cash</div>
              <div className="metric-value">${portfolio.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Positions Value</div>
              <div className="metric-value">${portfolio.positions_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Total Value</div>
              <div className="metric-value">${portfolio.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            </div>
            <div className={`metric-card ${portfolio.total_pnl >= 0 ? 'positive' : 'negative'}`}>
              <div className="metric-label">Total P&L</div>
              <div className="metric-value">
                ${portfolio.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                <span className="metric-percent">({portfolio.return_percent.toFixed(2)}%)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="paper-trading-content">
        {/* Order Placement */}
        <div className="order-section">
          <h2>Place Order</h2>
          <div className="order-form">
            <div className="form-row">
              <div className="form-group">
                <label>Symbol</label>
                <SymbolSelector
                  value={symbol}
                  onChange={setSymbol}
                  placeholder="Select symbol..."
                />
              </div>
              
              <div className="form-group">
                <label>Side</label>
                <select value={side} onChange={(e) => setSide(e.target.value as 'buy' | 'sell')}>
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </select>
              </div>

              <div className="form-group">
                <label>Order Type</label>
                <select value={orderType} onChange={(e) => setOrderType(e.target.value as 'market' | 'limit' | 'stop')}>
                  <option value="market">Market</option>
                  <option value="limit">Limit</option>
                  <option value="stop">Stop</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  min="1"
                  step="1"
                />
              </div>

              {orderType !== 'market' && (
                <div className="form-group">
                  <label>{orderType === 'limit' ? 'Limit Price' : 'Stop Price'}</label>
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(Number(e.target.value))}
                    min="0"
                    step="0.01"
                    placeholder={orderType === 'limit' ? 'Limit price' : 'Stop price'}
                  />
                </div>
              )}

              {currentPrice > 0 && (
                <div className="form-group">
                  <label>Current Price</label>
                  <div className="current-price">${currentPrice.toFixed(2)}</div>
                </div>
              )}
            </div>

            {currentPrice > 0 && orderType === 'market' && (
              <div className="order-summary">
                <div className="summary-item">
                  <span>Estimated Cost:</span>
                  <span>${(quantity * currentPrice).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
              </div>
            )}

            <button
              onClick={placeOrder}
              disabled={placingOrder || !symbol || quantity <= 0}
              className="place-order-button"
            >
              {placingOrder ? 'Placing Order...' : 'Place Order'}
            </button>
          </div>
        </div>

        {/* Positions */}
        <div className="positions-section">
          <h2>Positions ({positions.length})</h2>
          {positions.length === 0 ? (
            <div className="no-data">No open positions</div>
          ) : (
            <div className="positions-table">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Avg Entry</th>
                    <th>Current Price</th>
                    <th>Market Value</th>
                    <th>Unrealized P&L</th>
                    <th>Realized P&L</th>
                    <th>Total P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((position) => (
                    <tr key={position.symbol}>
                      <td className="symbol-cell">{position.symbol}</td>
                      <td>{position.quantity}</td>
                      <td>${position.average_entry_price.toFixed(2)}</td>
                      <td>${position.current_price.toFixed(2)}</td>
                      <td>${position.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                      <td className={position.unrealized_pnl >= 0 ? 'positive' : 'negative'}>
                        ${position.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className={position.realized_pnl >= 0 ? 'positive' : 'negative'}>
                        ${position.realized_pnl.toFixed(2)}
                      </td>
                      <td className={position.total_pnl >= 0 ? 'positive' : 'negative'}>
                        ${position.total_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Order History */}
        <div className="orders-section">
          <h2>Order History ({orders.length})</h2>
          {orders.length === 0 ? (
            <div className="no-data">No orders yet</div>
          ) : (
            <div className="orders-table">
              <table>
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Filled</th>
                    <th>Fill Price</th>
                    <th>Status</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.reverse().map((order) => (
                    <tr key={order.order_id}>
                      <td className="order-id">{order.order_id}</td>
                      <td>{order.symbol}</td>
                      <td className={order.side === 'buy' ? 'buy-side' : 'sell-side'}>
                        {order.side.toUpperCase()}
                      </td>
                      <td>{order.order_type.toUpperCase()}</td>
                      <td>{order.quantity}</td>
                      <td>{order.filled_quantity}</td>
                      <td>
                        {order.fill_price ? `$${order.fill_price.toFixed(2)}` : '-'}
                      </td>
                      <td className={`status-${order.status}`}>
                        {order.status.toUpperCase()}
                      </td>
                      <td>{new Date(order.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

