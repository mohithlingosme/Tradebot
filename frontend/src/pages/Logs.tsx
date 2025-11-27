import { useMemo, useState } from 'react'
import { useDashboardFeed } from '../hooks/useDashboardFeed'
import { LogEntry } from '../services/api'
import '../styles/DashboardSimple.css'

const formatTime = (ts: string) => new Date(ts).toLocaleTimeString()

function LogsPage() {
  const { logs, isLive, refreshSnapshot, isRefreshing, lastUpdated } = useDashboardFeed()
  const [level, setLevel] = useState<string>('ALL')
  const [maxRows, setMaxRows] = useState<number>(200)

  const filtered = useMemo<LogEntry[]>(() => {
    if (level === 'ALL') return logs
    return logs.filter((l) => l.level.toUpperCase() === level)
  }, [logs, level])
  const visibleLogs = useMemo(() => filtered.slice(0, maxRows), [filtered, maxRows])

  return (
    <div className="dashboard-shell">
      <div className="section-header">
        <div className="live-indicator" aria-label="live-status">
          <span className={`dot ${isLive ? '' : 'offline'}`} />
          {isLive ? 'Live logs' : 'Snapshot / polling'}
        </div>
        <div className="section-actions">
          {lastUpdated && <span className="faint-text">Updated {new Date(lastUpdated).toLocaleTimeString()}</span>}
          <button className="ghost-button" onClick={refreshSnapshot} disabled={isRefreshing}>
            {isRefreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="panel">
        <h2>Engine Logs</h2>
        <div style={{ marginBottom: 12 }}>
          <label htmlFor="log-filter" style={{ marginRight: 8 }}>Level:</label>
          <select id="log-filter" value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="ALL">All</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warn</option>
            <option value="ERROR">Error</option>
          </select>
          <label htmlFor="max-rows" style={{ marginLeft: 12, marginRight: 8 }}>Max rows:</label>
          <select id="max-rows" value={maxRows} onChange={(e) => setMaxRows(Number(e.target.value))}>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>
        <div className="logs-list">
          {visibleLogs.length === 0 ? (
            <div>No logs available.</div>
          ) : (
            visibleLogs.map((log, idx) => (
              <div
                key={`${log.timestamp}-${idx}`}
                className={`log-entry ${log.level.toLowerCase()}`}
              >
                <div>{formatTime(log.timestamp)}</div>
                <div className="log-level">{log.level}</div>
                <div>
                  <strong>{log.component || 'engine'}</strong>: {log.message}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default LogsPage
