import { useMemo, useState } from 'react'
import { useDashboardFeed } from '../hooks/useDashboardFeed'
import { OrderRow } from '../services/api'
import '../styles/DashboardSimple.css'

const formatTime = (ts?: string) => (ts ? new Date(ts).toLocaleTimeString() : '—')

const sideClass = (side: string) => (side === 'BUY' ? 'pill buy' : 'pill sell')

const statusLabel = (status?: string) => status?.toUpperCase() || 'UNKNOWN'

function OrdersPage() {
  const { orders, isLive } = useDashboardFeed()
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  const filtered = useMemo<OrderRow[]>(() => {
    if (statusFilter === 'ALL') return orders
    return orders.filter((o) => o.status?.toUpperCase() === statusFilter)
  }, [orders, statusFilter])

  return (
    <div className="dashboard-shell">
      <div className="live-indicator" aria-label="live-status">
        <span className={`dot ${isLive ? '' : 'offline'}`} />
        {isLive ? 'Live order feed' : 'Offline (last snapshot)'}
      </div>

      <div className="panel">
        <h2>Recent Orders</h2>
        <div style={{ marginBottom: 12 }}>
          <label htmlFor="status-filter" style={{ marginRight: 8 }}>Status:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All</option>
            <option value="NEW">New</option>
            <option value="FILLED">Filled</option>
            <option value="PARTIALLY_FILLED">Partially Filled</option>
            <option value="REJECTED">Rejected</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
        {filtered.length === 0 ? (
          <div>No orders yet.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((order) => (
                <tr key={order.id}>
                  <td>{formatTime(order.timestamp)}</td>
                  <td>{order.symbol}</td>
                  <td><span className={sideClass(order.side)}>{order.side}</span></td>
                  <td>{order.qty}</td>
                  <td>{order.price !== undefined ? order.price.toFixed(2) : '—'}</td>
                  <td><span className="pill status">{statusLabel(order.status)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default OrdersPage
