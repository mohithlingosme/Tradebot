import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const API_URL = 'http://localhost:8000'; // Assuming the backend runs on port 8000

function App() {
  const [user, setUser] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [symbol, setSymbol] = useState('AAPL');
  const [priceData, setPriceData] = useState(null);
  const [tradeSide, setTradeSide] = useState('buy');
  const [tradeQuantity, setTradeQuantity] = useState(1);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username: email,
        password: password,
      });
      setUser(response.data);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const fetchPortfolio = async () => {
    if (user) {
      try {
        const response = await axios.get(`${API_URL}/portfolio`, {
          headers: { Authorization: `Bearer ${user.access_token}` },
        });
        setPortfolio(response.data);
      } catch (error) {
        console.error('Failed to fetch portfolio:', error);
      }
    }
  };

  const fetchPriceData = async () => {
    try {
      const response = await axios.get(`${API_URL}/price/${symbol}`);
      setPriceData(response.data);
    } catch (error) {
      console.error('Failed to fetch price data:', error);
    }
  };

  const handleTrade = async (e) => {
    e.preventDefault();
    if (user) {
      try {
        await axios.post(
          `${API_URL}/trades`,
          {
            symbol: symbol,
            side: tradeSide,
            quantity: tradeQuantity,
          },
          {
            headers: { Authorization: `Bearer ${user.access_token}` },
          }
        );
        fetchPortfolio(); // Refresh portfolio after trade
      } catch (error) {
        console.error('Trade failed:', error);
      }
    }
  };

  useEffect(() => {
    fetchPortfolio();
    fetchPriceData();
  }, [user, symbol]);

  const chartData = {
    labels: priceData ? priceData.map((data) => new Date(data.timestamp).toLocaleTimeString()) : [],
    datasets: [
      {
        label: `${symbol} Price`,
        data: priceData ? priceData.map((data) => data.close) : [],
        borderColor: '#2196F3', // Sky Blue
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
      },
    ],
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FinBot</h1>
      </header>
      <main>
        {!user ? (
          <div className="login-form">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button type="submit">Login</button>
            </form>
          </div>
        ) : (
          <div className="dashboard">
            <div className="portfolio">
              <h2>Portfolio</h2>
              {portfolio ? (
                <div>
                  <p>Equity: ${portfolio.equity.toFixed(2)}</p>
                  <p>Profit/Loss: <span className={portfolio.pnl >= 0 ? 'positive' : 'negative'}>${portfolio.pnl.toFixed(2)}</span></p>
                  <h3>Positions</h3>
                  <ul>
                    {Object.entries(portfolio.positions).map(([symbol, quantity]) => (
                      <li key={symbol}>
                        {symbol}: {quantity}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p>Loading portfolio...</p>
              )}
            </div>
            <div className="trading">
              <h2>Trading</h2>
              <div className="chart-container">
                {priceData && <Line data={chartData} />}
              </div>
              <form onSubmit={handleTrade}>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                />
                <select value={tradeSide} onChange={(e) => setTradeSide(e.target.value)}>
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </select>
                <input
                  type="number"
                  value={tradeQuantity}
                  onChange={(e) => setTradeQuantity(parseInt(e.target.value))}
                  min="1"
                />
                <button type="submit" className={tradeSide === 'buy' ? 'buy-button' : 'sell-button'}>
                  {tradeSide.charAt(0).toUpperCase() + tradeSide.slice(1)}
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;