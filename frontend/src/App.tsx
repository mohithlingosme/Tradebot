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
            <button onClick={logout} className="nav-link logout-button">
              Logout
            </button>
          </nav>
        </header>
      )}
      <main className="app-main">
        <Outlet />
      </main>
      {isAuthenticated && <footer className="app-footer" />}
    </div>
  )
}

export default App
