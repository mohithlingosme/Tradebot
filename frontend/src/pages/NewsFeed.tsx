import { useState, useEffect } from 'react'
import axios from 'axios'
import '../styles/NewsFeed.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface NewsItem {
  id: string
  title: string
  summary: string
  source: string
  published_at: string
  url?: string
  sentiment?: 'positive' | 'negative' | 'neutral'
  symbols?: string[]
}

export default function NewsFeed() {
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(60) // seconds

  useEffect(() => {
    fetchNews()
    
    if (autoRefresh) {
      const interval = setInterval(fetchNews, refreshInterval * 1000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  const fetchNews = async () => {
    try {
      // Try to fetch from API (if endpoint exists)
      try {
        const token = localStorage.getItem('access_token')
        const response = await axios.get(`${API_BASE_URL}/news`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setNews(response.data.articles || response.data || [])
      } catch (err: any) {
        // Fallback to mock data
        setNews(generateMockNews())
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching news:', error)
      setNews(generateMockNews())
      setLoading(false)
    }
  }

  const generateMockNews = (): NewsItem[] => {
    return [
      {
        id: '1',
        title: 'Stock Market Hits New Highs Amid Economic Recovery',
        summary: 'Major indices reached record levels as economic indicators show strong recovery signals.',
        source: 'Financial Times',
        published_at: new Date().toISOString(),
        sentiment: 'positive',
        symbols: ['AAPL', 'GOOGL', 'MSFT']
      },
      {
        id: '2',
        title: 'Tech Stocks Volatility Expected This Week',
        summary: 'Analysts predict increased volatility in technology stocks due to upcoming earnings reports.',
        source: 'Bloomberg',
        published_at: new Date(Date.now() - 3600000).toISOString(),
        sentiment: 'neutral',
        symbols: ['AAPL', 'NVDA', 'TSLA']
      },
      {
        id: '3',
        title: 'Federal Reserve Signals Interest Rate Changes',
        summary: 'The Fed hints at potential rate adjustments in the coming months based on inflation data.',
        source: 'Reuters',
        published_at: new Date(Date.now() - 7200000).toISOString(),
        sentiment: 'neutral',
        symbols: []
      },
    ]
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000 / 60) // minutes
    
    if (diff < 1) return 'Just now'
    if (diff < 60) return `${diff} minute${diff > 1 ? 's' : ''} ago`
    if (diff < 1440) return `${Math.floor(diff / 60)} hour${Math.floor(diff / 60) > 1 ? 's' : ''} ago`
    return date.toLocaleDateString()
  }

  const getSentimentClass = (sentiment?: string) => {
    if (!sentiment) return ''
    return `sentiment-${sentiment}`
  }

  return (
    <div className="news-feed">
      <div className="news-header">
        <h1>Financial News Feed</h1>
        <div className="news-controls">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          {autoRefresh && (
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="refresh-select"
            >
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
              <option value={600}>10 minutes</option>
            </select>
          )}
          <button onClick={fetchNews} className="refresh-button">
            Refresh Now
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading news...</div>
      ) : (
        <div className="news-items">
          {news.length === 0 ? (
            <div className="no-news">No news articles available</div>
          ) : (
            news.map((item) => (
              <article key={item.id} className={`news-item ${getSentimentClass(item.sentiment)}`}>
                <div className="news-item-header">
                  <h3>{item.title}</h3>
                  <span className="news-source">{item.source}</span>
                </div>
                <p className="news-summary">{item.summary}</p>
                <div className="news-item-footer">
                  <span className="news-date">{formatDate(item.published_at)}</span>
                  {item.symbols && item.symbols.length > 0 && (
                    <div className="news-symbols">
                      {item.symbols.map((symbol) => (
                        <span key={symbol} className="symbol-tag">{symbol}</span>
                      ))}
                    </div>
                  )}
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="read-more">
                      Read more →
                    </a>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      )}

      {autoRefresh && (
        <div className="auto-refresh-indicator">
          <span className="indicator-dot"></span>
          Auto-refreshing every {refreshInterval} second{refreshInterval > 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}

