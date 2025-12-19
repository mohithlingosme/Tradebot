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
import type {
  IndicatorsResponse,
  PositionSnapshot,
  RegimeAnalytics,
  OrderBookAnalytics,
} from './api'
import {
  getIndicators,
  getPortfolio,
  getPositions,
  getRegimeAnalytics,
  getOrderBookAnalytics,
  placeTrade,
} from './api'

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

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const decimalFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const quantityFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
})

const percentFormatter = new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

const formatMetric = (value?: number | null, formatAsCurrency = false) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return PRICE_FALLBACK
  }
  return formatAsCurrency ? currencyFormatter.format(value) : decimalFormatter.format(value)
}

const formatQuantity = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return PRICE_FALLBACK
  }
  return quantityFormatter.format(value)
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

const REGIME_META: Record<string, { label: string; className: string }> = {
  high_volatility: { label: 'High Volatility', className: 'text-orange-400' },
  low_volatility: { label: 'Low Volatility', className: 'text-emerald-400' },
}

const ORDER_STATE_META: Record<string, { label: string; className: string }> = {
  bullish: { label: 'Bid Dominant', className: 'text-green-400' },
  bearish: { label: 'Ask Dominant', className: 'text-red-400' },
  balanced: { label: 'Balanced', className: 'text-slate-400' },
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
  const [positions, setPositions] = useState<PositionSnapshot[]>([])
  const [loadingIndicators, setLoadingIndicators] = useState(false)
  const [regimeAnalytics, setRegimeAnalytics] = useState<RegimeAnalytics | null>(null)
  const [orderBookAnalytics, setOrderBookAnalytics] = useState<OrderBookAnalytics | null>(null)
  const [loadingRegime, setLoadingRegime] = useState(false)
  const [loadingOrderBook, setLoadingOrderBook] = useState(false)
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

  const fetchRegimeSnapshot = useCallback(async () => {
    setLoadingRegime(true)
    try {
      const data = await getRegimeAnalytics(symbol)
      setRegimeAnalytics(data)
    } catch (err) {
      console.error(err)
      setRegimeAnalytics(null)
    } finally {
      setLoadingRegime(false)
    }
  }, [symbol])

  const fetchOrderBookSnapshot = useCallback(async () => {
    setLoadingOrderBook(true)
    try {
      const data = await getOrderBookAnalytics(symbol)
      setOrderBookAnalytics(data)
    } catch (err) {
      console.error(err)
      setOrderBookAnalytics(null)
    } finally {
      setLoadingOrderBook(false)
    }
  }, [symbol])

  useEffect(() => {
    fetchRegimeSnapshot()
    fetchOrderBookSnapshot()
  }, [fetchRegimeSnapshot, fetchOrderBookSnapshot])

  const fetchPositions = useCallback(async () => {
    try {
      const snapshot = await getPositions()
      setPositions(snapshot)
    } catch (err) {
      console.error(err)
    }
  }, [])

  useEffect(() => {
    fetchPositions()
  }, [fetchPositions])

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

  const regimeChartData = useMemo(() => {
    if (!regimeAnalytics) return []
    return regimeAnalytics.history.map((point) => ({
      time: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      probability: point.probability,
      label: point.label,
    }))
  }, [regimeAnalytics])

  const orderBookHistory = useMemo(() => {
    if (!orderBookAnalytics) return []
    return orderBookAnalytics.history.map((point) => ({
      time: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      imbalance: point.imbalance,
      state: point.state,
    }))
  }, [orderBookAnalytics])

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

  const activePosition = useMemo(() => {
    if (!positions.length) return null
    const normalizedSymbol = symbol.toUpperCase()
    return (
      positions.find((pos) => pos.symbol === normalizedSymbol) ??
      positions.find((pos) => pos.status === 'open') ??
      positions[positions.length - 1]
    )
  }, [positions, symbol])

  const positionMeta = useMemo(() => {
    if (!activePosition) return null
    const directionLabel =
      activePosition.direction === 'long'
        ? 'Long'
        : activePosition.direction === 'short'
          ? 'Short'
          : 'Flat'
    const directionClass =
      activePosition.direction === 'long'
        ? 'text-green-400'
        : activePosition.direction === 'short'
          ? 'text-red-400'
          : 'text-slate-400'
    const statusClass = activePosition.status === 'open' ? 'text-green-400' : 'text-slate-400'
    return { directionLabel, directionClass, statusClass }
  }, [activePosition])

  const handleTrade = async (side: 'buy' | 'sell') => {
    try {
      await placeTrade({ symbol, qty, side })
      alert(`${side.toUpperCase()} order placed`)
      const refreshed = await getPortfolio()
      setPortfolio(refreshed)
      await fetchPositions()
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
            <p className={`text-2xl font-bold mt-2 ${item.color}`}>{formatMetric(item.val, true)}</p>
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
                      tickFormatter={(value) => currencyFormatter.format(Number(value))}
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                      width={70}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                      labelStyle={{ color: '#94a3b8' }}
                      formatter={(value: number, name) => [
                        name === 'price'
                          ? currencyFormatter.format(value)
                          : decimalFormatter.format(value),
                        formatIndicatorLabel(String(name)),
                      ]}
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
                        formatter={(value: number) => [
                          decimalFormatter.format(value),
                          formatIndicatorLabel(key),
                        ]}
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
                {priceSnapshot ? formatMetric(priceSnapshot.price, true) : PRICE_FALLBACK}
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

          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4">📊 Position Monitor</h2>
            {activePosition ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400">Asset</p>
                    <p className="text-2xl font-semibold">{activePosition.symbol}</p>
                  </div>
                  {positionMeta && (
                    <span className={`text-sm font-semibold ${positionMeta.directionClass}`}>
                      {positionMeta.directionLabel}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-slate-400">Position Size</p>
                    <p className="text-lg font-semibold">
                      {formatQuantity(Math.abs(activePosition.qty))}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Entry Price</p>
                    <p className="text-lg font-semibold">{formatMetric(activePosition.entry_price, true)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Mark Price</p>
                    <p className="text-lg font-semibold">{formatMetric(activePosition.mark_price, true)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">Status</p>
                    <p className={`text-lg font-semibold ${positionMeta?.statusClass ?? 'text-slate-400'}`}>
                      {activePosition.status === 'open' ? 'Open' : 'Closed'}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-slate-500">
                  Updated {activePosition.last_updated ? new Date(activePosition.last_updated).toLocaleString() : 'N/A'}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">
                No trades placed yet. Execute a trade to see live position details.
              </p>
            )}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mt-10">
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-slate-400">Volatility Regime</p>
              <h3
                className={`text-2xl font-bold ${
                  regimeAnalytics ? REGIME_META[regimeAnalytics.current_regime]?.className ?? 'text-slate-200' : 'text-slate-500'
                }`}
              >
                {regimeAnalytics
                  ? REGIME_META[regimeAnalytics.current_regime]?.label ?? regimeAnalytics.current_regime
                  : 'Awaiting Data'}
              </h3>
              <p className="text-sm text-slate-400">
                Confidence:{' '}
                {regimeAnalytics ? percentFormatter.format(regimeAnalytics.probability) : PRICE_FALLBACK}
              </p>
              <p className="text-sm text-slate-400">
                ATR: {regimeAnalytics ? formatMetric(regimeAnalytics.atr, true) : PRICE_FALLBACK}
              </p>
            </div>
            <button
              onClick={fetchRegimeSnapshot}
              className="flex items-center gap-2 text-slate-400 hover:text-white text-sm"
            >
              <RefreshCcw size={14} /> {loadingRegime ? 'Updating...' : 'Refresh'}
            </button>
          </div>
          <div className="h-56">
            {regimeAnalytics && regimeChartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={regimeChartData}>
                  <CartesianGrid strokeDasharray="4 4" stroke="#1e293b" />
                  <XAxis dataKey="time" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis
                    tickFormatter={(value) => percentFormatter.format(Number(value))}
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    width={60}
                    domain={[0, 1]}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                    labelStyle={{ color: '#94a3b8' }}
                    formatter={(value: number) => [percentFormatter.format(value), 'Probability']}
                  />
                  <Area
                    type="monotone"
                    dataKey="probability"
                    stroke="#a855f7"
                    fill="#a855f7"
                    fillOpacity={0.2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-700 rounded">
                {loadingRegime ? 'Fetching regime analytics...' : 'No regime data available'}
              </div>
            )}
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-slate-400">Order Book State</p>
              <h3
                className={`text-2xl font-bold ${
                  orderBookAnalytics
                    ? ORDER_STATE_META[orderBookAnalytics.state]?.className ?? 'text-slate-200'
                    : 'text-slate-500'
                }`}
              >
                {orderBookAnalytics
                  ? ORDER_STATE_META[orderBookAnalytics.state]?.label ?? orderBookAnalytics.state
                  : 'Awaiting Data'}
              </h3>
              <p className="text-sm text-slate-400">
                Imbalance:{' '}
                {orderBookAnalytics
                  ? percentFormatter.format(orderBookAnalytics.imbalance)
                  : PRICE_FALLBACK}
              </p>
              <p className="text-sm text-slate-400">
                Spread:{' '}
                {orderBookAnalytics ? formatMetric(orderBookAnalytics.spread, true) : PRICE_FALLBACK}
              </p>
            </div>
            <button
              onClick={fetchOrderBookSnapshot}
              className="flex items-center gap-2 text-slate-400 hover:text-white text-sm"
            >
              <RefreshCcw size={14} /> {loadingOrderBook ? 'Updating...' : 'Refresh'}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div>
              <p className="text-xs text-slate-400">Best Bid</p>
              <p className="text-lg font-semibold">
                {orderBookAnalytics ? formatMetric(orderBookAnalytics.best_bid, true) : PRICE_FALLBACK}
              </p>
              <p className="text-xs text-slate-500">
                Buy Vol: {orderBookAnalytics ? formatQuantity(orderBookAnalytics.buy_pressure) : PRICE_FALLBACK}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Best Ask</p>
              <p className="text-lg font-semibold">
                {orderBookAnalytics ? formatMetric(orderBookAnalytics.best_ask, true) : PRICE_FALLBACK}
              </p>
              <p className="text-xs text-slate-500">
                Sell Vol: {orderBookAnalytics ? formatQuantity(orderBookAnalytics.sell_pressure) : PRICE_FALLBACK}
              </p>
            </div>
          </div>
          <div className="h-40 mb-4">
            {orderBookHistory.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={orderBookHistory}>
                  <CartesianGrid strokeDasharray="4 4" stroke="#1e293b" />
                  <XAxis dataKey="time" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis
                    tickFormatter={(value) => percentFormatter.format(Number(value))}
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    width={60}
                    domain={[-1, 1]}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                    labelStyle={{ color: '#94a3b8' }}
                    formatter={(value: number) => [percentFormatter.format(value), 'Imbalance']}
                  />
                  <Line type="monotone" dataKey="imbalance" stroke="#34d399" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-700 rounded">
                {loadingOrderBook ? 'Fetching order book data...' : 'No order book data available'}
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-slate-400 mb-1">Bids</p>
              <div className="space-y-1 border border-slate-700 rounded p-2 h-32 overflow-y-auto">
                {orderBookAnalytics?.bids && orderBookAnalytics.bids.length ? (
                  orderBookAnalytics.bids.slice(0, 6).map((level, idx) => (
                    <div key={`bid-${idx}`} className="flex justify-between text-green-300">
                      <span>{formatMetric(level.price, true)}</span>
                      <span>{formatQuantity(level.size)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500">No bids</p>
                )}
              </div>
            </div>
            <div>
              <p className="text-slate-400 mb-1">Asks</p>
              <div className="space-y-1 border border-slate-700 rounded p-2 h-32 overflow-y-auto">
                {orderBookAnalytics?.asks && orderBookAnalytics.asks.length ? (
                  orderBookAnalytics.asks.slice(0, 6).map((level, idx) => (
                    <div key={`ask-${idx}`} className="flex justify-between text-red-300">
                      <span>{formatMetric(level.price, true)}</span>
                      <span>{formatQuantity(level.size)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500">No asks</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
