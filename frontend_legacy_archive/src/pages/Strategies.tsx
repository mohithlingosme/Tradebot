import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import api from '@/lib/api';

interface Strategy {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error';
  roi: number;
  lastUpdate: string;
}

const Strategies = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await api.get('/strategies');
        setStrategies(response.data);
      } catch (error) {
        console.error("Failed to fetch strategies:", error);
      }
    };

    fetchStrategies();
  }, []);

  const toggleStrategy = (id: string) => {
    // This part will need to be updated to make an API call to the backend
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
