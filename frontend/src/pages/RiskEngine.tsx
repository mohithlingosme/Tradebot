import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { RiskCard } from '../components/widgets/RiskCard';

const RiskEngine = () => {
  const mockAlerts = [
    { id: '1', message: 'Max drawdown exceeded 5%', severity: 'high' as const },
    { id: '2', message: 'Position size too large for AAPL', severity: 'medium' as const },
    { id: '3', message: 'Daily loss limit approaching', severity: 'low' as const },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Risk Engine</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Exposure</span>
                <span className="text-lg font-semibold">$2,450,000</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div className="bg-blue-600 h-3 rounded-full" style={{ width: '65%' }}></div>
              </div>
              <div className="text-sm text-muted-foreground">65% of max exposure limit</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">VaR (95%)</p>
                <p className="text-lg font-semibold text-red-600">-$45,230</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Max Drawdown</p>
                <p className="text-lg font-semibold text-orange-600">-3.2%</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                <p className="text-lg font-semibold text-green-600">1.85</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Beta</p>
                <p className="text-lg font-semibold">0.92</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Portfolio Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { symbol: 'AAPL', exposure: 450000, percentage: 18.4 },
                { symbol: 'GOOGL', exposure: 380000, percentage: 15.5 },
                { symbol: 'MSFT', exposure: 320000, percentage: 13.1 },
                { symbol: 'TSLA', exposure: 280000, percentage: 11.4 },
                { symbol: 'Others', exposure: 1020000, percentage: 41.6 },
              ].map((item) => (
                <div key={item.symbol} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{item.symbol}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-muted-foreground">
                      ${item.exposure.toLocaleString()}
                    </span>
                    <span className="text-sm font-medium">{item.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <RiskCard
          title="Active Alerts"
          exposure={2450000}
          alerts={mockAlerts}
        />
      </div>
    </div>
  );
};

export default RiskEngine;
