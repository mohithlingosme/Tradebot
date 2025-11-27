import { useMemo } from 'react'
import { useDashboardFeed } from '../hooks/useDashboardFeed'
import '../styles/DashboardSimple.css'

const fmtCurrency = (value: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value)

function PositionsPage() {
  const { positions, isLive, refreshSnapshot, isRefreshing, lastUpdated } = useDashboardFeed()
  const activePositions = useMemo(() => positions.filter((p) => p.quantity !== 0), [positions])
  const totals = useMemo(() => {
    const unrealized = activePositions.reduce((acc, p) => acc + p.pnl, 0)
    return { unrealized }
  }, [activePositions])

  return (
    <div className="dashboard-shell">
      <div className="section-header">
        <div className="live-indicator" aria-label="live-status">
          <span className={`dot ${isLive ? '' : 'offline'}`} />
          {isLive ? 'Live positions' : 'Snapshot / polling'}
        </div>
        <div className="section-actions">
          {lastUpdated && <span className="faint-text">Updated {new Date(lastUpdated).toLocaleTimeString()}</span>}
          <button className="ghost-button" onClick={refreshSnapshot} disabled={isRefreshing}>
            {isRefreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="panel">
        <h2>Open Positions</h2>
        {activePositions.length === 0 ? (
          <div>No open positions.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Qty</th>
                <th>Avg Price</th>
                <th>Last Price</th>
                <th>Unrealized P&L</th>
              </tr>
            </thead>
            <tbody>
              {activePositions.map((pos) => (
                <tr key={pos.symbol}>
                  <td>{pos.symbol}</td>
                  <td>{pos.quantity}</td>
                  <td>{pos.avg_price.toFixed(2)}</td>
                  <td>{pos.current_price.toFixed(2)}</td>
                  <td className={pos.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                    {fmtCurrency(pos.pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan={4} style={{ textAlign: 'right' }}>Total Unrealized</th>
                <th className={totals.unrealized >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                  {fmtCurrency(totals.unrealized)}
                </th>
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </div>
  )
}

export default PositionsPage
