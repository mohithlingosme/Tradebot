import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, RefreshCcw, TrendingUp } from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { IndicatorsResponse } from './api'
import { getIndicators, getPortfolio, placeTrade } from './api'

type Portfolio = {
  cash: number
  equity: number
  buying_power: number
}

type ChartRow = Record<string, string | number | null>

const PRICE_FALLBACK = '--'
const COLOR_PALETTE = [
  '#f87171',
  '#34d399',
  '#60a5fa',
  '#facc15',
  '#c084fc',
  '#fb7185',
  '#14b8a6',
  '#a855f7',
  '#f97316',
  '#22d3ee',
]

const formatMetric = (value?: number | null, formatAsCurrency = false) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return PRICE_FALLBACK
  }
  return formatAsCurrency ? `$${value.toFixed(2)}` : value.toFixed(2)
}

const formatIndicatorLabel = (key: string) =>
  key
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')

type TrendDirection = 'positive' | 'negative' | 'neutral'

const computeDirection = (current?: number | null, previous?: number | null): TrendDirection => {
  if (
    current === undefined ||
    current === null ||
    Number.isNaN(current) ||
    previous === undefined ||
    previous === null ||
    Number.isNaN(previous)
  ) {
    return 'neutral'
  }
  if (current > previous) return 'positive'
  if (current < previous) return 'negative'
  return 'neutral'
}

const DIRECTION_META: Record<TrendDirection, { label: string; className: string }> = {
  positive: { label: 'Positive', className: 'text-green-400' },
  negative: { label: 'Negative', className: 'text-red-400' },
  neutral: { label: 'Neutral', className: 'text-slate-400' },
}

const extractTrend = (series: Array<number | null>): { value: number | null; direction: TrendDirection } => {
  if (!series.length) {
    return { value: null, direction: 'neutral' }
  }
  let current: number | null = null
  let previous: number | null = null
  for (let idx = series.length - 1; idx >= 0; idx -= 1) {
    if (series[idx] !== null && series[idx] !== undefined) {
      current = series[idx]
      break
    }
  }
  if (current !== null) {
    for (let idx = series.length - 2; idx >= 0; idx -= 1) {
      if (series[idx] !== null && series[idx] !== undefined) {
        previous = series[idx]
        break
      }
    }
  }
  return { value: current, direction: computeDirection(current, previous) }
}

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [symbol, setSymbol] = useState('BTC/USD')
  const [qty, setQty] = useState(1)
  const [indicatorData, setIndicatorData] = useState<IndicatorsResponse | null>(null)
  const [availableIndicators, setAvailableIndicators] = useState<string[]>([])
  const [selectedOverlays, setSelectedOverlays] = useState<string[]>([])
  const [selectedOscillators, setSelectedOscillators] = useState<string[]>([])
  const [priceSnapshot, setPriceSnapshot] = useState<{ price: number; time: string } | null>(null)
  const [loadingIndicators, setLoadingIndicators] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    getPortfolio()
      .then(setPortfolio)
      .catch((err) => {
        console.error(err)
        navigate('/')
      })
  }, [navigate])

  const fetchIndicators = useCallback(async () => {
    setLoadingIndicators(true)
    try {
      const data = await getIndicators(symbol)
      setIndicatorData(data)
      const keys = Object.keys(data.indicators).sort()
      setAvailableIndicators(keys)
      setSelectedOverlays((prev) => prev.filter((key) => keys.includes(key)))
      setSelectedOscillators((prev) => prev.filter((key) => keys.includes(key)))
      if (!keys.length) {
        setSelectedOverlays([])
        setSelectedOscillators([])
      }
      if (data.timestamp.length && data.price.length) {
        const lastIndex = data.timestamp.length - 1
        setPriceSnapshot({
          time: data.timestamp[lastIndex],
          price: data.price[lastIndex],
        })
      } else {
        setPriceSnapshot(null)
      }
    } catch (err) {
      console.error(err)
      alert('Unable to fetch indicator data.')
    } finally {
      setLoadingIndicators(false)
    }
  }, [symbol])

  useEffect(() => {
    fetchIndicators()
  }, [fetchIndicators])

  const chartRows: ChartRow[] = useMemo(() => {
    if (!indicatorData) return []
    const rows: ChartRow[] = indicatorData.timestamp.map((time, idx) => ({
      time,
      label: new Date(time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      price: indicatorData.price[idx] ?? null,
    }))
    Object.entries(indicatorData.indicators).forEach(([key, series]) => {
      rows.forEach((row, idx) => {
        row[key] = series[idx] ?? null
      })
    })
    return rows
  }, [indicatorData])

  const indicatorColorMap = useMemo(() => {
    const map = new Map<string, string>()
    availableIndicators.forEach((key, idx) => {
      map.set(key, COLOR_PALETTE[idx % COLOR_PALETTE.length])
    })
    return map
  }, [availableIndicators])

  const indicatorMetrics = useMemo(() => {
  if (!indicatorData) {
    const placeholder = [
      {
        label: 'Price',
        value: null,
        direction: 'neutral' as TrendDirection,
        currency: true,
      },
    ]
    const rest = availableIndicators.map((label) => ({
      label: formatIndicatorLabel(label),
      value: null,
      direction: 'neutral' as TrendDirection,
      currency: false,
    }))
    return [...placeholder, ...rest]
  }
  const metrics = [
    {
      label: 'Price',
      ...extractTrend(indicatorData.price.map((value) => value ?? null)),
      currency: true,
    },
  ]
  availableIndicators.forEach((key) => {
    const series = indicatorData.indicators[key] ?? []
    metrics.push({
      label: formatIndicatorLabel(key),
      ...extractTrend(series),
      currency: false,
    })
  })
  return metrics
}, [indicatorData, availableIndicators])

  const handleTrade = async (side: 'buy' | 'sell') => {
    try {
      await placeTrade({ symbol, qty, side })
      alert(`${side.toUpperCase()} order placed`)
      const refreshed = await getPortfolio()
      setPortfolio(refreshed)
    } catch (err) {
      console.error(err)
      alert('Trade Failed')
    }
  }

  if (!portfolio) {
    return <div className="p-10 text-white">Loading Financial Data...</div>
  }

  const handleSelectChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
    setter: (value: string[]) => void
  ) => {
    const options = Array.from(event.target.selectedOptions).map((opt) => opt.value)
    setter(options)
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

      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 mb-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-1">Indicator Selector</h2>
            <p className="text-slate-400 text-sm">Choose overlays and oscillators to visualize.</p>
          </div>
          <div className="flex gap-2">
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="bg-slate-700 p-2 rounded text-white border border-slate-600"
              placeholder="Symbol (e.g. BTC/USD)"
            />
            <button
              onClick={fetchIndicators}
              className="bg-blue-600 px-4 rounded hover:bg-blue-500 flex items-center gap-2 disabled:opacity-50"
              disabled={loadingIndicators}
            >
              <RefreshCcw size={16} /> {loadingIndicators ? 'Loading...' : 'Fetch'}
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Overlay Indicators</label>
            <select
              multiple
              value={selectedOverlays}
              onChange={(event) => handleSelectChange(event, setSelectedOverlays)}
              className="w-full bg-slate-700 border border-slate-600 rounded p-2 h-32"
            >
              {availableIndicators.map((key) => (
                <option key={key} value={key}>
                  {formatIndicatorLabel(key)}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Oscillator Indicators</label>
            <select
              multiple
              value={selectedOscillators}
              onChange={(event) => handleSelectChange(event, setSelectedOscillators)}
              className="w-full bg-slate-700 border border-slate-600 rounded p-2 h-32"
            >
              {availableIndicators.map((key) => (
                <option key={key} value={key}>
                  {formatIndicatorLabel(key)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="flex flex-col xl:flex-row gap-8">
        <div className="flex-1 space-y-8">
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4">📡 Market View</h2>
            <div className="h-80">
              {chartRows.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartRows}>
                    <defs>
                      <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.6} />
                        <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="4 4" stroke="#1e293b" />
                    <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                    <YAxis
                      tickFormatter={(value) => `$${Number(value).toFixed(2)}`}
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      width={70}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                      labelStyle={{ color: '#94a3b8' }}
                      formatter={(value: number, name) => [`${value.toFixed(2)}`, formatIndicatorLabel(String(name))]}
                    />
                    <Area
                      type="monotone"
                      dataKey="price"
                      stroke="#38bdf8"
                      fillOpacity={1}
                      fill="url(#priceGradient)"
                      strokeWidth={2}
                    />
                    {selectedOverlays.map((key) => (
                      <Line
                        key={key}
                        type="monotone"
                        dataKey={key}
                        stroke={indicatorColorMap.get(key) ?? '#facc15'}
                        dot={false}
                        strokeWidth={2}
                      />
                    ))}
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-700 rounded">
                  {loadingIndicators ? 'Loading indicator data...' : 'No indicator data available.'}
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
            <h2 className="text-lg font-semibold mb-2">Oscillator Panels</h2>
            {selectedOscillators.length ? (
              selectedOscillators.map((key) => (
                <div key={key} className="h-48 border border-slate-700 rounded-lg p-2">
                  <p className="text-xs text-slate-400 mb-1">{formatIndicatorLabel(key)}</p>
                  <ResponsiveContainer width="100%" height="90%">
                    <LineChart data={chartRows}>
                      <CartesianGrid strokeDasharray="4 4" stroke="#1e293b" />
                      <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} width={60} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                        labelStyle={{ color: '#94a3b8' }}
                        formatter={(value: number) => [`${value.toFixed(2)}`, formatIndicatorLabel(key)]}
                      />
                      <Line
                        type="monotone"
                        dataKey={key}
                        stroke={indicatorColorMap.get(key) ?? '#f97316'}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ))
            ) : (
              <div className="h-24 flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-700 rounded">
                Select oscillator indicators to visualize them here.
              </div>
            )}
          </div>
        </div>

        <div className="xl:w-80 space-y-6">
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h2 className="text-lg font-semibold mb-4">Control Panel</h2>
            <div className="p-4 bg-slate-700/40 rounded mb-4">
              <p className="text-xs text-slate-400 mb-1">Last Update</p>
              <div className="text-2xl font-semibold">
                {priceSnapshot ? `$${priceSnapshot.price.toFixed(2)}` : PRICE_FALLBACK}
              </div>
              <p className="text-xs text-slate-500">
                {priceSnapshot ? new Date(priceSnapshot.time).toLocaleString() : 'Awaiting data'}
              </p>
            </div>
            <div className="space-y-4 text-sm max-h-[420px] overflow-y-auto pr-2">
              {indicatorMetrics.map((metric) => {
                const meta = DIRECTION_META[metric.direction]
                return (
                  <div
                    key={metric.label}
                    className="flex items-center justify-between border-b border-slate-700 pb-2 last:border-b-0"
                  >
                    <div className="text-slate-300">{metric.label}</div>
                    <div className="text-right">
                      <div className="text-white font-semibold">
                        {formatMetric(metric.value, metric.currency)}
                      </div>
                      <div className={`text-xs ${meta.className}`}>{meta.label}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4">⚡ Quick Execution</h2>
            <div className="mb-4">
              <label className="block text-xs text-slate-400 mb-1">Quantity</label>
              <input
                type="number"
                value={qty}
                onChange={(e) => setQty(Number(e.target.value))}
                className="w-full bg-slate-700 p-2 rounded text-white border border-slate-600"
                min={0.01}
                step={0.01}
              />
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
    </div>
  )
}
