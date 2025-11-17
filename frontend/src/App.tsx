import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import './styles/App.css'

function App() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <div className="app">
      {isAuthenticated && (
        <header className="app-header">
          <h1>Finbot</h1>
          <nav className="app-nav">
            <NavLink to="/" end className="nav-link">
              Dashboard
            </NavLink>
            <NavLink to="/watchlist" className="nav-link">
              Watchlist
            </NavLink>
            <NavLink to="/news" className="nav-link">
              News
            </NavLink>
            <NavLink to="/ai-assistant" className="nav-link">
              AI Assistant
            </NavLink>
            <NavLink to="/paper-trading" className="nav-link">
              Paper Trading
            </NavLink>
            <NavLink to="/settings" className="nav-link">
              Settings
            </NavLink>
            <button onClick={logout} className="nav-link logout-button">
              Logout
            </button>
          </nav>
        </header>
      )}
      <main className="app-main">
        <Outlet />
      </main>
      {isAuthenticated && (
        <footer className="app-footer">
          <p>&copy; 2024 Finbot Market Data App</p>
        </footer>
      )}
    </div>
  )
}

export default App
