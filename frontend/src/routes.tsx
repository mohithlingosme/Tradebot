import { lazy, Suspense } from 'react'
import type { ComponentType, LazyExoticComponent, ReactElement } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'

const App = lazy(() => import('./App'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Watchlist = lazy(() => import('./pages/Watchlist'))
const Settings = lazy(() => import('./pages/Settings'))
const NewsFeed = lazy(() => import('./pages/NewsFeed'))
const AIAssistant = lazy(() => import('./pages/AIAssistant'))
const PaperTrading = lazy(() => import('./pages/PaperTrading'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const Landing = lazy(() => import('./pages/Landing'))

const LoadingFallback = () => (
  <div className="route-loading">Loading…</div>
)

const lazyLoad = (Component: LazyExoticComponent<ComponentType<any>>): ReactElement => (
  <Suspense fallback={<LoadingFallback />}>
    <Component />
  </Suspense>
)

const router = createBrowserRouter([
  {
    path: '/',
    element: lazyLoad(App),
    children: [
      {
        index: true,
        element: (
          <ProtectedRoute>
            {lazyLoad(Dashboard)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'watchlist',
        element: (
          <ProtectedRoute>
            {lazyLoad(Watchlist)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'settings',
        element: (
          <ProtectedRoute>
            {lazyLoad(Settings)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'news',
        element: (
          <ProtectedRoute>
            {lazyLoad(NewsFeed)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'ai-assistant',
        element: (
          <ProtectedRoute>
            {lazyLoad(AIAssistant)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'paper-trading',
        element: (
          <ProtectedRoute>
            {lazyLoad(PaperTrading)}
          </ProtectedRoute>
        ),
      },
      { path: 'landing', element: lazyLoad(Landing) },
      { path: 'login', element: lazyLoad(Login) },
      { path: 'register', element: lazyLoad(Register) },
      { path: 'forgot-password', element: lazyLoad(ForgotPassword) },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])

export default router
