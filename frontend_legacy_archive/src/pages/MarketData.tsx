import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { CandleChart } from '../components/charts/CandleChart';

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
}

const mockMarketData: MarketData[] = [
  {
    symbol: 'AAPL',
    price: 175.43,
    change: 2.15,
    changePercent: 1.24,
    volume: 45230000,
    marketCap: 2800000000000,
  },
  {
    symbol: 'GOOGL',
    price: 138.21,
    change: -1.23,
    changePercent: -0.88,
    volume: 28340000,
    marketCap: 1750000000000,
  },
  {
    symbol: 'MSFT',
    price: 378.85,
    change: 5.67,
    changePercent: 1.52,
    volume: 32150000,
    marketCap: 2820000000000,
  },
  {
    symbol: 'TSLA',
    price: 248.42,
    change: -8.31,
    changePercent: -3.24,
    volume: 67890000,
    marketCap: 790000000000,
  },
  {
    symbol: 'AMZN',
    price: 144.05,
    change: 1.89,
    changePercent: 1.33,
    volume: 41230000,
    marketCap: 1480000000000,
  },
];

const MarketData = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [timeframe, setTimeframe] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const filteredData = mockMarketData.filter(item =>
    item.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedData = mockMarketData.find(item => item.symbol === selectedSymbol);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Market Data</h1>
        <div className="flex items-center space-x-4">
          <Button variant={autoRefresh ? 'default' : 'outline'} onClick={() => setAutoRefresh(!autoRefresh)}>
            Auto Refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{selectedSymbol} Chart</CardTitle>
                <div className="flex space-x-2">
                  {['1m', '5m', '15m', '1h', '4h', '1d'].map((tf) => (
                    <Button
                      key={tf}
                      variant={timeframe === tf ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setTimeframe(tf)}
                    >
                      {tf}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <CandleChart symbol={selectedSymbol} timeframe={timeframe} />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Symbol Search</CardTitle>
            </CardHeader>
            <CardContent>
              <Input
                placeholder="Search symbols..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Market Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredData.map((item) => (
                  <div
                    key={item.symbol}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedSymbol === item.symbol
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                    onClick={() => setSelectedSymbol(item.symbol)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{item.symbol}</span>
                      <span className="text-sm">${item.price.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span
                        className={`text-sm ${
                          item.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {item.change >= 0 ? '+' : ''}{item.change.toFixed(2)}
                      </span>
                      <span
                        className={`text-sm ${
                          item.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        ({item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {selectedData && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{selectedData.symbol} Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Volume</span>
                    <span className="text-sm font-medium">
                      {(selectedData.volume / 1000000).toFixed(1)}M
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Market Cap</span>
                    <span className="text-sm font-medium">
                      ${(selectedData.marketCap / 1000000000000).toFixed(1)}T
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">P/E Ratio</span>
                    <span className="text-sm font-medium">28.5</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarketData;
