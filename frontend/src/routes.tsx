import { lazy, Suspense } from 'react'
import type { ComponentType, LazyExoticComponent, ReactElement } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'

const App = lazy(() => import('./App'))
const Home = lazy(() => import('./pages/Home'))
const Orders = lazy(() => import('./pages/Orders'))
const Positions = lazy(() => import('./pages/Positions'))
const Logs = lazy(() => import('./pages/Logs'))
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
            {lazyLoad(Home)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'orders',
        element: (
          <ProtectedRoute>
            {lazyLoad(Orders)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'positions',
        element: (
          <ProtectedRoute>
            {lazyLoad(Positions)}
          </ProtectedRoute>
        ),
      },
      {
        path: 'logs',
        element: (
          <ProtectedRoute>
            {lazyLoad(Logs)}
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
