import SummaryCard from '../components/SummaryCard'
import { useDashboardFeed } from '../hooks/useDashboardFeed'
import '../styles/DashboardSimple.css'

const fmtCurrency = (value: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value)

const fmtPct = (value: number) => `${(value * 100).toFixed(1)}%`

function Home() {
  const { pnl, positions, strategy, risk, isLive } = useDashboardFeed()
  const activePositions = positions.filter((p) => p.quantity !== 0)
  const riskUsed = risk.used_pct ?? 0

  return (
    <div className="dashboard-shell">
      <div className="live-indicator" aria-label="live-status">
        <span className={`dot ${isLive ? '' : 'offline'}`} />
        {isLive ? 'Live updates' : 'Offline (using latest snapshot)'}
      </div>

      <div className="summary-grid">
        <SummaryCard
          title="Total P&L"
          value={fmtCurrency(pnl.total ?? 0)}
          subtitle={`Realized ${fmtCurrency(pnl.realized ?? 0)} · Unrealized ${fmtCurrency(pnl.unrealized ?? 0)}`}
          tone={(pnl.total ?? 0) >= 0 ? 'positive' : 'negative'}
        />
        <SummaryCard
          title="Active Positions"
          value={activePositions.length.toString()}
          subtitle="Open positions across all symbols"
          tone={activePositions.length > 0 ? 'default' : 'muted'}
        />
        <SummaryCard
          title="Strategy"
          value={`${strategy.name ?? 'Strategy'} · ${strategy.state ?? 'UNKNOWN'}`}
          subtitle={strategy.since ? `since ${new Date(strategy.since).toLocaleString()}` : undefined}
          tone={strategy.state === 'RUNNING' ? 'positive' : strategy.state === 'PAUSED' ? 'muted' : 'negative'}
        />
        <SummaryCard
          title="Risk Status"
          value={`${fmtPct(riskUsed)} of max daily loss`}
          subtitle={risk.circuit_breaker ? 'Circuit breaker TRIGGERED' : 'Circuit breaker OFF'}
          tone={risk.circuit_breaker ? 'negative' : 'default'}
        />
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
          </table>
        )}
      </div>
    </div>
  )
}

export default Home
