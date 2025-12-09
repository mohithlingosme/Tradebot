import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

interface Strategy {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error';
  roi: number;
  lastUpdate: string;
}

const mockStrategies: Strategy[] = [
  { id: '1', name: 'EMA Crossover', status: 'running', roi: 12.5, lastUpdate: '2024-01-15 10:30' },
  { id: '2', name: 'RSI Momentum', status: 'stopped', roi: -2.3, lastUpdate: '2024-01-14 15:45' },
  { id: '3', name: 'Bollinger Bands', status: 'running', roi: 8.7, lastUpdate: '2024-01-15 09:15' },
];

const Strategies = () => {
  const [strategies, setStrategies] = useState(mockStrategies);

  const toggleStrategy = (id: string) => {
    setStrategies(prev =>
      prev.map(strategy =>
        strategy.id === id
          ? { ...strategy, status: strategy.status === 'running' ? 'stopped' : 'running' }
          : strategy
      )
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-600';
      case 'stopped':
        return 'text-gray-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Strategies</h1>
        <Button>Add New Strategy</Button>
      </div>

      <div className="grid gap-4">
        {strategies.map((strategy) => (
          <Card key={strategy.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{strategy.name}</CardTitle>
                <div className="flex items-center space-x-4">
                  <span className={`text-sm font-medium ${getStatusColor(strategy.status)}`}>
                    {strategy.status.toUpperCase()}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleStrategy(strategy.id)}
                  >
                    {strategy.status === 'running' ? 'Stop' : 'Start'}
                  </Button>
                  <Button variant="outline" size="sm">
                    Edit
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">ROI</p>
                  <p className={`text-lg font-semibold ${strategy.roi >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {strategy.roi >= 0 ? '+' : ''}{strategy.roi}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Last Update</p>
                  <p className="text-lg font-semibold">{strategy.lastUpdate}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Strategies;
