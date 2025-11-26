import './SummaryCard.css'

interface SummaryCardProps {
  title: string
  value: string
  subtitle?: string
  tone?: 'default' | 'positive' | 'negative' | 'muted'
}

export function SummaryCard({ title, value, subtitle, tone = 'default' }: SummaryCardProps) {
  return (
    <div className={`summary-card ${tone}`}>
      <div className="summary-title">{title}</div>
      <div className="summary-value">{value}</div>
      {subtitle && <div className="summary-subtitle">{subtitle}</div>}
    </div>
  )
}

export default SummaryCard
