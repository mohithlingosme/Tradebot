import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, RefreshCcw, TrendingUp } from 'lucide-react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { getPortfolio, getPrice, placeTrade } from './api'

type Portfolio = {
  cash: number
  equity: number
  buying_power: number
}

type PriceData = {
  price: number
  timestamp?: string
  time?: string
}

type PriceHistoryPoint = {
  label: string
  price: number
}

const PRICE_POLL_INTERVAL = 5000
const MAX_HISTORY_POINTS = 30

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [priceData, setPriceData] = useState<PriceData | null>(null)
  const [priceHistory, setPriceHistory] = useState<PriceHistoryPoint[]>([])
  const [symbol, setSymbol] = useState('AAPL')
  const [qty, setQty] = useState(1)
  const navigate = useNavigate()

  useEffect(() => {
    fetchPortfolio()
  }, [])

  useEffect(() => {
    setPriceHistory([])
  }, [symbol])

  const fetchPortfolio = async () => {
    try {
      const data = await getPortfolio()
      setPortfolio(data)
    } catch (err) {
      console.error(err)
      navigate('/')
    }
  }

  const fetchLivePrice = useCallback(async () => {
    const data = await getPrice(symbol)
    setPriceData(data)

    const timestamp = data.time ?? data.timestamp ?? new Date().toISOString()
    const formattedLabel = new Date(timestamp).toLocaleTimeString([], {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })

    setPriceHistory((prev) => {
      const next = [...prev, { label: formattedLabel, price: Number(data.price) }]
      if (next.length > MAX_HISTORY_POINTS) {
        next.shift()
      }
      return next
    })
  }, [symbol])

  useEffect(() => {
    let isMounted = true

    const tick = () => {
      fetchLivePrice().catch((err) => {
        if (isMounted) {
          console.error(err)
        }
      })
    }

    tick()
    const interval = setInterval(tick, PRICE_POLL_INTERVAL)

    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [fetchLivePrice])

  const handleGetPrice = async () => {
    try {
      await fetchLivePrice()
    } catch (err) {
      console.error(err)
      alert('Symbol not found')
    }
  }

  const handleTrade = async (side: 'buy' | 'sell') => {
    try {
      await placeTrade({ symbol, qty, side })
      alert(`${side.toUpperCase()} Order Placed!`)
      fetchPortfolio()
    } catch (err) {
      console.error(err)
      alert('Trade Failed')
    }
  }

  if (!portfolio) {
    return <div className="p-10 text-white">Loading Financial Data...</div>
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <header className="flex justify-between items-center mb-10 border-b border-slate-700 pb-4">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <TrendingUp className="text-green-400" /> Finbot Terminal
        </h1>
        <button
          onClick={() => {
            localStorage.clear()
            navigate('/')
          }}
          className="flex items-center gap-2 text-slate-400 hover:text-white"
        >
          <LogOut size={18} /> Logout
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[
          { label: 'Cash Balance', val: portfolio.cash, color: 'text-green-400' },
          { label: 'Portfolio Equity', val: portfolio.equity, color: 'text-blue-400' },
          { label: 'Buying Power', val: portfolio.buying_power, color: 'text-purple-400' },
        ].map((item) => (
          <div key={item.label} className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h3 className="text-slate-400 text-sm font-medium">{item.label}</h3>
            <p className={`text-2xl font-bold mt-2 ${item.color}`}>${item.val.toLocaleString()}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <h2 className="text-xl font-bold mb-4">📡 Live Market Data</h2>
          <div className="flex gap-2 mb-4">
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="bg-slate-700 p-2 rounded text-white w-full border border-slate-600"
              placeholder="Symbol (e.g. BTC/USD)"
            />
            <button onClick={handleGetPrice} className="bg-blue-600 px-4 rounded hover:bg-blue-500">
              <RefreshCcw size={20} />
            </button>
          </div>
          {priceData && (
            <div className="text-center p-4 bg-slate-700/50 rounded animate-pulse">
              <div className="text-4xl font-bold">${priceData.price}</div>
              <div className="text-sm text-slate-400 mt-1">
                {priceData.timestamp ?? priceData.time}
              </div>
            </div>
          )}
          <div className="mt-6">
            <div className="flex items-center justify-between text-sm text-slate-400 mb-2">
              <span>Live Price Trace</span>
              <span>{symbol}</span>
            </div>
            <div className="h-64">
              {priceHistory.length > 1 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={priceHistory}>
                    <CartesianGrid strokeDasharray="4 4" stroke="#334155" />
                    <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                    <YAxis
                      tickFormatter={(value) => `$${Number(value).toFixed(2)}`}
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      width={70}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                      labelStyle={{ color: '#94a3b8' }}
                      formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#34d399"
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-700 rounded">
                  Waiting for real-time ticks...
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <h2 className="text-xl font-bold mb-4">⚡ Quick Execution</h2>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <label className="block text-xs text-slate-400 mb-1">Quantity</label>
              <input
                type="number"
                value={qty}
                onChange={(e) => setQty(Number(e.target.value))}
                className="w-full bg-slate-700 p-2 rounded text-white border border-slate-600"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => handleTrade('buy')}
              className="bg-green-600 py-3 rounded font-bold hover:bg-green-500 transition"
            >
              BUY {symbol}
            </button>
            <button
              onClick={() => handleTrade('sell')}
              className="bg-red-600 py-3 rounded font-bold hover:bg-red-500 transition"
            >
              SELL {symbol}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
