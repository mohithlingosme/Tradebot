import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import MarketData from './pages/MarketData';
import Strategies from './pages/Strategies';
import RiskEngine from './pages/RiskEngine';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/layout/Sidebar';
import Navbar from './components/layout/Navbar';
import PageContainer from './components/layout/PageContainer';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <div className="min-h-screen bg-background">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/" element={
                  <ProtectedRoute>
                    <div className="flex">
                      <Sidebar />
                      <div className="flex-1 flex flex-col">
                        <Navbar />
                        <PageContainer>
                          <Routes>
                            <Route index element={<Dashboard />} />
                            <Route path="market-data" element={<MarketData />} />
                            <Route path="strategies" element={<Strategies />} />
                            <Route path="risk-engine" element={<RiskEngine />} />
                            <Route path="logs" element={<Logs />} />
                            <Route path="settings" element={<Settings />} />
                          </Routes>
                        </PageContainer>
                      </div>
                    </div>
                  </ProtectedRoute>
                } />
              </Routes>
            </div>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
