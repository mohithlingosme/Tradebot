interface StatItem {
  label: string;
  value: string;
  status?: 'success' | 'warning' | 'error';
}

interface StatCardProps {
  title: string;
  items: StatItem[];
}

export const StatCard = ({ title, items }: StatCardProps) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'warning':
        return 'text-yellow-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-foreground';
    }
  };

  return (
    <div className="bg-card rounded-lg p-6 border">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{item.label}</span>
            <span className={`text-sm font-medium ${getStatusColor(item.status)}`}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
