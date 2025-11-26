import { useMemo, useState } from 'react'
import { useDashboardFeed } from '../hooks/useDashboardFeed'
import { LogEntry } from '../services/api'
import '../styles/DashboardSimple.css'

const formatTime = (ts: string) => new Date(ts).toLocaleTimeString()

function LogsPage() {
  const { logs, isLive } = useDashboardFeed()
  const [level, setLevel] = useState<string>('ALL')

  const filtered = useMemo<LogEntry[]>(() => {
    if (level === 'ALL') return logs
    return logs.filter((l) => l.level.toUpperCase() === level)
  }, [logs, level])

  return (
    <div className="dashboard-shell">
      <div className="live-indicator" aria-label="live-status">
        <span className={`dot ${isLive ? '' : 'offline'}`} />
        {isLive ? 'Live logs' : 'Offline (last snapshot)'}
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
        </div>
        <div className="logs-list">
          {filtered.length === 0 ? (
            <div>No logs available.</div>
          ) : (
            filtered.map((log, idx) => (
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
