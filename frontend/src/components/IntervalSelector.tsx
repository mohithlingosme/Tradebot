interface IntervalSelectorProps {
  value: string
  onChange: (interval: string) => void
}

const intervals = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '1wk', label: '1 Week' },
  { value: '1mo', label: '1 Month' },
]

function IntervalSelector({ value, onChange }: IntervalSelectorProps) {
  return (
    <div className="interval-selector">
      <label htmlFor="interval">Interval:</label>
      <select
        id="interval"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {intervals.map(interval => (
          <option key={interval.value} value={interval.value}>
            {interval.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default IntervalSelector
