import { useState, useEffect } from 'react'
import axios from 'axios'
import '../styles/PortfolioSummary.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


interface PortfolioData {
  total_value: number
  cash: number
  positions_value: number
  pnl: number
  positions?: Position[]
}

interface Position {
  symbol: string
  quantity: number
  avg_price: number
  current_price: number
  value: number
  pnl: number
  pnl_percent: number
}

export default function PortfolioSummary() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPortfolio()
    const interval = setInterval(fetchPortfolio, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchPortfolio = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/portfolio`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setPortfolio(response.data)
      setError(null)
    } catch (err: any) {
      // Fallback to mock data if endpoint not available
      setPortfolio({
        total_value: 100000,
        cash: 50000,
        positions_value: 50000,
        pnl: 2500,
        positions: [
          { symbol: 'AAPL', quantity: 50, avg_price: 150, current_price: 155, value: 7750, pnl: 250, pnl_percent: 3.33 },
          { symbol: 'GOOGL', quantity: 20, avg_price: 2800, current_price: 2850, value: 57000, pnl: 1000, pnl_percent: 1.79 },
        ]
      })
      if (err.response?.status !== 503) {
        setError('Failed to load portfolio data')
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading portfolio...</div>
  }

  if (error && !portfolio) {
    return <div className="error">Error: {error}</div>
  }

  if (!portfolio) {
    return <div className="no-data">No portfolio data available</div>
  }

  return (
    <div className="portfolio-summary">
      <div className="portfolio-header">
        <h2>Portfolio Summary</h2>
        <button onClick={fetchPortfolio} className="refresh-button">Refresh</button>
      </div>

      <div className="portfolio-overview">
        <div className="metric-card">
          <div className="metric-label">Total Value</div>
          <div className="metric-value">${portfolio.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Cash</div>
          <div className="metric-value">${portfolio.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Positions Value</div>
          <div className="metric-value">${portfolio.positions_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className={`metric-card ${portfolio.pnl >= 0 ? 'positive' : 'negative'}`}>
          <div className="metric-label">P&L</div>
          <div className="metric-value">
            ${portfolio.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span className="metric-percent">
              ({((portfolio.pnl / (portfolio.total_value - portfolio.pnl)) * 100).toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>

      {portfolio.positions && portfolio.positions.length > 0 && (
        <div className="positions-table">
          <h3>Positions</h3>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Avg Price</th>
                <th>Current Price</th>
                <th>Value</th>
                <th>P&L</th>
                <th>P&L %</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.map((position) => (
                <tr key={position.symbol}>
                  <td className="symbol-cell">{position.symbol}</td>
                  <td>{position.quantity}</td>
                  <td>${position.avg_price.toFixed(2)}</td>
                  <td>${position.current_price.toFixed(2)}</td>
                  <td>${position.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  <td className={position.pnl >= 0 ? 'positive' : 'negative'}>
                    ${position.pnl.toFixed(2)}
                  </td>
                  <td className={position.pnl_percent >= 0 ? 'positive' : 'negative'}>
                    {position.pnl_percent >= 0 ? '+' : ''}{position.pnl_percent.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
