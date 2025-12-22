import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

// Lazy load pages for better performance
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const MarketData = lazy(() => import('./pages/MarketData'));
const Strategies = lazy(() => import('./pages/Strategies'));
const RiskEngine = lazy(() => import('./pages/RiskEngine'));
const Logs = lazy(() => import('./pages/Logs'));
const Settings = lazy(() => import('./pages/Settings'));

export const routes: RouteObject[] = [
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    path: '/',
    element: <Dashboard />,
  },
  {
    path: '/market-data',
    element: <MarketData />,
  },
  {
    path: '/strategies',
    element: <Strategies />,
  },
  {
    path: '/risk-engine',
    element: <RiskEngine />,
  },
  {
    path: '/logs',
    element: <Logs />,
  },
  {
    path: '/settings',
    element: <Settings />,
  },
];
