import Plot from 'react-plotly.js'
import { Candle } from '../services/api'

interface CandleChartProps {
  data: Candle[]
  symbol?: string
  interval?: string
  realTime?: boolean
}

function CandleChart({ data, symbol = '', interval = '1d', realTime = false }: CandleChartProps) {
  if (!data || data.length === 0) {
    return <div className="no-data">No data available</div>
  }

  const dates = data.map(candle => new Date(candle.timestamp))
  const opens = data.map(candle => candle.open)
  const highs = data.map(candle => candle.high)
  const lows = data.map(candle => candle.low)
  const closes = data.map(candle => candle.close)
  const volumes = data.map(candle => candle.volume)

  const candlestickData = {
    x: dates,
    open: opens,
    high: highs,
    low: lows,
    close: closes,
    type: 'candlestick' as const,
    name: 'Candles',
    increasing: { line: { color: 'green' } },
    decreasing: { line: { color: 'red' } },
  }

  const volumeData = {
    x: dates,
    y: volumes,
    type: 'bar' as const,
    name: 'Volume',
    yaxis: 'y2',
    marker: { color: 'rgba(0, 0, 255, 0.5)' },
  }

  const layout = {
    title: { text: `${symbol || data[0]?.symbol || 'Symbol'} Candlestick Chart (${interval})${realTime ? ' - Live' : ''}` },
    xaxis: {
      title: { text: 'Time' },
      type: 'date' as const,
    },
    yaxis: {
      title: { text: 'Price' },
      autorange: true,
    },
    yaxis2: {
      title: { text: 'Volume' },
      overlaying: 'y' as const,
      side: 'right' as const,
      autorange: true,
    },
    showlegend: true,
    height: 600,
    margin: { l: 50, r: 50, t: 50, b: 50 },
  }


  return (
    <div className="candle-chart">
      <Plot
        data={[candlestickData, volumeData]}
        layout={layout}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        config={{ responsive: true }}
      />
    </div>
  )
}

export default CandleChart
