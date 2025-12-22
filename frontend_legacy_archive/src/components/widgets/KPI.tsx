interface KPIProps {
  title: string;
  value: number;
  change: number;
  format: 'currency' | 'percentage' | 'number';
}

export const KPI = ({ title, value, change, format }: KPIProps) => {
  const formatValue = (val: number, fmt: string) => {
    switch (fmt) {
      case 'currency':
        return `$${val.toLocaleString()}`;
      case 'percentage':
        return `${val.toFixed(2)}%`;
      default:
        return val.toLocaleString();
    }
  };

  const isPositive = change >= 0;
  const changeColor = isPositive ? 'text-green-600' : 'text-red-600';
  const changeIcon = isPositive ? '↑' : '↓';

  return (
    <div className="bg-card rounded-lg p-6 border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{formatValue(value, format)}</p>
        </div>
        <div className={`text-sm font-medium ${changeColor}`}>
          {changeIcon} {Math.abs(change).toFixed(2)}%
        </div>
      </div>
    </div>
  );
};
