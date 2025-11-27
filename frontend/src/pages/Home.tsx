import { Link } from 'react-router-dom'
import SummaryCard from '../components/SummaryCard'
import { useDashboardFeed } from '../hooks/useDashboardFeed'
import '../styles/DashboardSimple.css'

const fmtCurrency = (value: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value)

const fmtPct = (value: number) => `${(value * 100).toFixed(1)}%`

const badgeTone = (riskUsed: number, circuitBreaker: boolean) => {
  if (circuitBreaker || riskUsed >= 1) return 'breached'
  if (riskUsed >= 0.8) return 'warning'
  return 'safe'
}

function Home() {
  const { pnl, positions, strategy, risk, isLive, lastUpdated } = useDashboardFeed()
  const activePositions = positions.filter((p) => p.quantity !== 0)
  const topPositions = activePositions.slice(0, 5)
  const riskUsed = risk.used_pct ?? 0
  const riskBadge = badgeTone(riskUsed, risk.circuit_breaker)
  const strategyTone = strategy.state === 'RUNNING' ? 'safe' : strategy.state === 'ERROR' ? 'breached' : 'warning'

  return (
    <div className="dashboard-shell">
      <div className="section-header">
        <div className="live-indicator" aria-label="live-status">
          <span className={`dot ${isLive ? '' : 'offline'}`} />
          {isLive ? 'Live updates' : 'Realtime paused · using snapshot'}
        </div>
        {lastUpdated && <span className="faint-text">Updated {new Date(lastUpdated).toLocaleTimeString()}</span>}
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
          title="Strategy State"
          value={`${strategy.state ?? 'UNKNOWN'}`}
          subtitle={strategy.name ? `Mode: ${strategy.name}` : undefined}
          tone={strategy.state === 'RUNNING' ? 'positive' : strategy.state === 'PAUSED' ? 'muted' : 'negative'}
        />
        <SummaryCard
          title="Risk Status"
          value={`${fmtPct(riskUsed)} of daily loss limit`}
          subtitle={risk.circuit_breaker ? 'Circuit breaker TRIGGERED' : 'Circuit breaker OFF'}
          tone={riskBadge === 'breached' ? 'negative' : riskBadge === 'warning' ? 'default' : 'positive'}
        />
      </div>

      <div className="panel-grid">
        <div className="panel">
          <div className="section-header">
            <h2>Active Positions</h2>
            {activePositions.length > 0 && (
              <Link to="/positions" className="inline-link">
                View all
              </Link>
            )}
          </div>
          {activePositions.length === 0 ? (
            <div>No open positions.</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Qty</th>
                  <th>Entry</th>
                  <th>LTP</th>
                  <th>P&L</th>
                </tr>
              </thead>
              <tbody>
                {topPositions.map((pos) => (
                  <tr key={pos.symbol}>
                    <td>{pos.symbol}</td>
                    <td>
                      <span className={pos.quantity >= 0 ? 'pill buy' : 'pill sell'}>
                        {pos.quantity >= 0 ? 'LONG' : 'SHORT'}
                      </span>
                    </td>
                    <td>{Math.abs(pos.quantity)}</td>
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

        <div className="panel">
          <div className="section-header">
            <h2>Strategy & Risk</h2>
          </div>
          <div className="stack">
            <div className="status-row">
              <div>
                <div className="label">Strategy</div>
                <div className="value">{strategy.name ?? 'Strategy'} </div>
                {strategy.since && (
                  <div className="muted">{`since ${new Date(strategy.since).toLocaleString()}`}</div>
                )}
              </div>
              <span className={`badge ${strategyTone}`}>
                {strategy.state ?? 'UNKNOWN'}
              </span>
            </div>
            <div className="status-row">
              <div>
                <div className="label">Daily loss</div>
                <div className="muted">Using {fmtPct(riskUsed)} of limit</div>
              </div>
              <span className={`badge ${riskBadge}`}>{riskBadge === 'breached' ? 'BREACHED' : riskBadge.toUpperCase()}</span>
            </div>
            <div className="status-row">
              <div>
                <div className="label">Circuit breaker</div>
                <div className="muted">{risk.circuit_breaker ? 'Triggered' : 'Off'}</div>
              </div>
              <span className={`badge ${risk.circuit_breaker ? 'breached' : 'safe'}`}>
                {risk.circuit_breaker ? 'TRIGGERED' : 'NORMAL'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
