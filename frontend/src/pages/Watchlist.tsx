import { useState } from 'react'
import SymbolSelector from '../components/SymbolSelector'
import WatchlistItem from '../components/WatchlistItem'
import { useWatchlist } from '../hooks/useWatchlist'

function Watchlist() {
  const [newSymbol, setNewSymbol] = useState('')
  const { watchlist, addToWatchlist, removeFromWatchlist } = useWatchlist()
  const handleAddSymbol = () => {
    if (newSymbol && !watchlist.includes(newSymbol)) {
      addToWatchlist(newSymbol)
      setNewSymbol('')
    }
  }

  return (
    <div className="watchlist">
      <h2>My Watchlist</h2>

      <div className="add-symbol">
        <SymbolSelector
          value={newSymbol}
          onChange={setNewSymbol}
          placeholder="Add symbol to watchlist..."
        />
        <button
          onClick={handleAddSymbol}
          disabled={!newSymbol || watchlist.includes(newSymbol)}
        >
          Add
        </button>
      </div>

      <div className="watchlist-items">
        {watchlist.length === 0 ? (
          <div className="no-items">No symbols in watchlist. Add some to get started!</div>
        ) : (
          watchlist.map(symbol => (
            <WatchlistItem
              key={symbol}
              symbol={symbol}
              onRemove={() => removeFromWatchlist(symbol)}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default Watchlist
