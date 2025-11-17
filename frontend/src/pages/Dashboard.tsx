import { useState } from 'react'
import SymbolSelector from '../components/SymbolSelector'
import IntervalSelector from '../components/IntervalSelector'
import CandleChart from '../components/CandleChart'
import PortfolioSummary from '../components/PortfolioSummary'
import WatchlistWidget from '../components/WatchlistWidget'
import { useMarketData } from '../hooks/useMarketData'
import '../styles/Dashboard.css'

function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [selectedInterval, setSelectedInterval] = useState('1d')
  const [activeTab, setActiveTab] = useState<'chart' | 'portfolio' | 'watchlist'>('chart')

  const { candlesData, marketData, isLoading, isConnected } = useMarketData(
    selectedSymbol,
    selectedInterval
  )

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol)
  }

  const handleIntervalChange = (interval: string) => {
    setSelectedInterval(interval)
  }

  const currentPrice = selectedSymbol && marketData[selectedSymbol]?.price

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <div className="dashboard-tabs">
          <button
            className={activeTab === 'chart' ? 'active' : ''}
            onClick={() => setActiveTab('chart')}
          >
            Market Data
          </button>
          <button
            className={activeTab === 'portfolio' ? 'active' : ''}
            onClick={() => setActiveTab('portfolio')}
          >
            Portfolio
          </button>
          <button
            className={activeTab === 'watchlist' ? 'active' : ''}
            onClick={() => setActiveTab('watchlist')}
          >
            Watchlist
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {activeTab === 'chart' && (
          <div className="market-data-section">
            <div className="controls">
              <SymbolSelector
                value={selectedSymbol}
                onChange={handleSymbolChange}
                placeholder="Select symbol..."
              />
              <IntervalSelector
                value={selectedInterval}
                onChange={handleIntervalChange}
              />

              {selectedSymbol && (
                <div className="price-display">
                  <span className="symbol">{selectedSymbol}</span>
                  {currentPrice && (
                    <span className="price">${currentPrice.toFixed(2)}</span>
                  )}
                  <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
                    {isConnected ? '● Live' : '● Offline'}
                  </span>
                </div>
              )}
            </div>

            <div className="chart-container">
              {isLoading ? (
                <div className="loading">Loading chart data...</div>
              ) : candlesData ? (
                <CandleChart data={candlesData.data} symbol={selectedSymbol} interval={selectedInterval} />
              ) : (
                <div className="no-data">Select a symbol to view the chart</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'portfolio' && (
          <div className="portfolio-section">
            <PortfolioSummary />
          </div>
        )}

        {activeTab === 'watchlist' && (
          <div className="watchlist-section">
            <WatchlistWidget />
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
