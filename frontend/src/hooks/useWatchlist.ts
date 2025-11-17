import { useState, useEffect } from 'react'

const WATCHLIST_STORAGE_KEY = 'market-data-watchlist'

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<string[]>([])

  // Load watchlist from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(WATCHLIST_STORAGE_KEY)
    if (stored) {
      try {
        setWatchlist(JSON.parse(stored))
      } catch (error) {
        console.error('Failed to parse watchlist from localStorage:', error)
      }
    }
  }, [])

  // Save watchlist to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist))
  }, [watchlist])

  const addToWatchlist = (symbol: string) => {
    if (!watchlist.includes(symbol)) {
      setWatchlist(prev => [...prev, symbol])
    }
  }

  const removeFromWatchlist = (symbol: string) => {
    setWatchlist(prev => prev.filter(s => s !== symbol))
  }

  const isInWatchlist = (symbol: string) => {
    return watchlist.includes(symbol)
  }

  return {
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist
  }
}
