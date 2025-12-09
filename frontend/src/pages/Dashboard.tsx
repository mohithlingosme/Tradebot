import { useQuery } from 'react-query';
import { api } from '../lib/api';
import { KPI } from '../components/widgets/KPI';
import { StatCard } from '../components/widgets/StatCard';
import { RiskCard } from '../components/widgets/RiskCard';
import { CandleChart } from '../components/charts/CandleChart';

const Dashboard = () => {
  const { data: dashboardData, isLoading } = useQuery('dashboard', () =>
    api.get('/dashboard').then(res => res.data)
  );

  if (isLoading) {
    return <div className="flex items-center justify-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPI
          title="Portfolio Value"
          value={dashboardData?.portfolioValue || 0}
          change={dashboardData?.portfolioChange || 0}
          format="currency"
        />
        <KPI
          title="Realized P&L"
          value={dashboardData?.realizedPnL || 0}
          change={dashboardData?.realizedPnLChange || 0}
          format="currency"
        />
        <KPI
          title="Unrealized P&L"
          value={dashboardData?.unrealizedPnL || 0}
          change={dashboardData?.unrealizedPnLChange || 0}
          format="currency"
        />
        <KPI
          title="Daily Volatility"
          value={dashboardData?.dailyVolatility || 0}
          change={dashboardData?.volatilityChange || 0}
          format="percentage"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Live Market Chart</h3>
          <CandleChart symbol="AAPL" />
        </div>

        <div className="space-y-4">
          <StatCard
            title="System Health"
            items={[
              { label: 'API Status', value: 'Online', status: 'success' },
              { label: 'Ingestion Status', value: 'Running', status: 'success' },
              { label: 'Latency', value: '45ms', status: 'warning' },
            ]}
          />

          <RiskCard
            title="Risk Overview"
            exposure={dashboardData?.exposure || 0}
            alerts={dashboardData?.alerts || []}
          />
        </div>
      </div>

      <div className="bg-card rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Events</h3>
        <div className="space-y-2">
          {dashboardData?.recentEvents?.map((event: any, index: number) => (
            <div key={index} className="flex items-center justify-between py-2 border-b">
              <div>
                <p className="font-medium">{event.message}</p>
                <p className="text-sm text-muted-foreground">{event.timestamp}</p>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                event.type === 'success' ? 'bg-green-100 text-green-800' :
                event.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {event.type}
              </span>
            </div>
          )) || []}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
