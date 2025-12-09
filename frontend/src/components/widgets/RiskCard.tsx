interface RiskCardProps {
  title: string;
  exposure: number;
  alerts: Array<{
    id: string;
    message: string;
    severity: 'low' | 'medium' | 'high';
  }>;
}

export const RiskCard = ({ title, exposure, alerts }: RiskCardProps) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="bg-card rounded-lg p-6 border">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">Current Exposure</span>
          <span className="text-lg font-semibold">${exposure.toLocaleString()}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full"
            style={{ width: `${Math.min((exposure / 1000000) * 100, 100)}%` }}
          ></div>
        </div>
      </div>

      <div className="space-y-2">
        <h4 className="text-sm font-medium">Active Alerts</h4>
        {alerts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active alerts</p>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-2 rounded text-sm ${getSeverityColor(alert.severity)}`}
            >
              {alert.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
