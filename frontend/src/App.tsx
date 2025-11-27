import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import './styles/App.css'

function App() {
  const { isAuthenticated, logout, username } = useAuth()
  const [showLegalModal, setShowLegalModal] = useState(false)

  if (!isAuthenticated) {
    return (
      <div className="app">
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    )
  }

  return (
    <div className="app app-authenticated">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">Finbot</div>
          {username && <div className="user">{username}</div>}
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            Home
          </NavLink>
          <NavLink to="/orders" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            Orders
          </NavLink>
          <NavLink to="/positions" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            Positions
          </NavLink>
          <NavLink to="/logs" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            Logs
          </NavLink>
        </nav>
        <button onClick={logout} className="nav-link logout-button">
          Logout
        </button>
      </aside>
      <div className="app-content">
        <header className="app-topbar">
          <div>
            <div className="topbar-title">Trading Dashboard</div>
            <div className="topbar-subtitle">Live P&amp;L · Positions · Orders · Logs</div>
          </div>
          <button className="link-button" onClick={() => setShowLegalModal(true)}>
            Legal &amp; Risk Info
          </button>
        </header>
        <div className="risk-banner">
          <div>
            Finbot is an experimental AI trading tool. It does not provide licensed investment advice.
            Trading equities and derivatives involves substantial risk of loss. Consult a SEBI-registered
            investment adviser before making decisions.
          </div>
          <button className="link-button" onClick={() => setShowLegalModal(true)}>
            View details
          </button>
        </div>
        <main className="app-main">
          <Outlet />
        </main>
      </div>
      {showLegalModal && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="legal-modal">
            <div className="legal-modal__header">
              <h3>Legal &amp; Risk Information</h3>
              <button className="link-button" onClick={() => setShowLegalModal(false)}>Close</button>
            </div>
            <div className="legal-modal__body">
              <p>
                This tool is intended for personal/experimental use. It is not licensed investment advice.
                No SEBI registration or other regulatory approval is implied.
              </p>
              <p>
                For public distribution or client-facing use, separate legal and regulatory approvals are required.
                Trading F&amp;O and intraday involves high risk; only risk capital should be used.
              </p>
              <p>
                This tool is currently not cleared for public distribution or advisory use without proper legal
                and regulatory review.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
