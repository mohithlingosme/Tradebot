import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useWatchlist } from '../hooks/useWatchlist'
import WatchlistItem from './WatchlistItem'
import '../styles/WatchlistWidget.css'

interface WatchlistWidgetProps {
  limit?: number
}

function WatchlistWidget({ limit = 5 }: WatchlistWidgetProps) {
  const [expanded, setExpanded] = useState(false)
  const { watchlist, removeFromWatchlist } = useWatchlist()

  const toggleExpanded = () => {
    setExpanded(!expanded)
  }


  const limitedWatchlist = expanded ? watchlist : watchlist.slice(0, limit)

  return (
    <div className="watchlist-widget">
      <div className="widget-header" onClick={toggleExpanded}>
        <h3>
          Watchlist
          <span className="item-count"> ({watchlist.length})</span>
        </h3>
        <button className="expand-button">{expanded ? '▲' : '▼'}</button>
      </div>
      <ul className="watchlist-items">
        {limitedWatchlist.map(symbol => (
          <WatchlistItem
            key={symbol}
            symbol={symbol}
            onRemove={removeFromWatchlist}
          />
        ))}
      </ul>
      {!expanded && watchlist.length > limit && (
        <div className="show-more">
          <Link to="/watchlist" onClick={toggleExpanded}>
            Show All ({watchlist.length})
          </Link>
        </div>
      )}
    </div>
  )
}

export default WatchlistWidget
