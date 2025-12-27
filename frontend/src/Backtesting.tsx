import React, { useState, useEffect } from 'react';
import { api } from './api';

interface BacktestConfig {
  strategy: string;
  symbols: string[];
  startDate: string;
  endDate: string;
  parameters: Record<string, any>;
}

interface BacktestResult {
  id: string;
  status: 'running' | 'completed' | 'failed';
  config: BacktestConfig;
  metrics?: {
    totalReturn: number;
    sharpeRatio: number;
    winRate: number;
    totalTrades: number;
    maxDrawdown: number;
  };
  equityCurve?: Array<{ date: string; equity: number; drawdown: number }>;
  trades?: Array<{
    symbol: string;
    side: string;
    quantity: number;
    entryPrice: number;
    exitPrice: number;
    pnl: number;
    entryTime: string;
    exitTime: string;
  }>;
  error?: string;
}

interface Strategy {
  name: string;
  description: string;
  parameters: Array<{
    name: string;
    type: 'number' | 'select' | 'boolean';
    default: any;
    options?: string[];
    min?: number;
    max?: number;
    step?: number;
  }>;
}

const Backtesting: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [config, setConfig] = useState<BacktestConfig>({
    strategy: '',
    symbols: [],
    startDate: '',
    endDate: '',
    parameters: {}
  });
  const [runningBacktests, setRunningBacktests] = useState<BacktestResult[]>([]);
  const [completedBacktests, setCompletedBacktests] = useState<BacktestResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [symbols, setSymbols] = useState<string[]>([]);

  useEffect(() => {
    loadStrategies();
    loadSymbols();
    loadBacktestHistory();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await api.get('/backtest/strategies');
      setStrategies(response.data);
    } catch (error) {
      console.error('Failed to load strategies:', error);
      // Mock strategies for demo
      setStrategies([
        {
          name: 'SMA Crossover',
          description: 'Simple moving average crossover strategy',
          parameters: [
            { name: 'fastPeriod', type: 'number', default: 20, min: 5, max: 50, step: 1 },
            { name: 'slowPeriod', type: 'number', default: 50, min: 20, max: 200, step: 5 },
            { name: 'stopLoss', type: 'number', default: 2.0, min: 0.5, max: 10.0, step: 0.1 },
            { name: 'takeProfit', type: 'number', default: 5.0, min: 1.0, max: 20.0, step: 0.5 }
          ]
        },
        {
          name: 'RSI Mean Reversion',
          description: 'RSI-based mean reversion strategy',
          parameters: [
            { name: 'rsiPeriod', type: 'number', default: 14, min: 7, max: 21, step: 1 },
            { name: 'overboughtLevel', type: 'number', default: 70, min: 60, max: 80, step: 1 },
            { name: 'oversoldLevel', type: 'number', default: 30, min: 20, max: 40, step: 1 },
            { name: 'positionSize', type: 'number', default: 100, min: 10, max: 1000, step: 10 }
          ]
        }
      ]);
    }
  };

  const loadSymbols = async () => {
    try {
      const response = await api.get('/backtest/symbols');
      setSymbols(response.data);
    } catch (error) {
      console.error('Failed to load symbols:', error);
      // Mock symbols for demo
      setSymbols(['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'LT', 'KOTAKBANK', 'AXISBANK']);
    }
  };

  const loadBacktestHistory = async () => {
    try {
      const response = await api.get('/backtest/history');
      const results = response.data;
      setCompletedBacktests(results.filter((r: BacktestResult) => r.status === 'completed'));
      setRunningBacktests(results.filter((r: BacktestResult) => r.status === 'running'));
    } catch (error) {
      console.error('Failed to load backtest history:', error);
    }
  };

  const handleStrategyChange = (strategyName: string) => {
    const strategy = strategies.find(s => s.name === strategyName);
    if (strategy) {
      const defaultParams: Record<string, any> = {};
      strategy.parameters.forEach(param => {
        defaultParams[param.name] = param.default;
      });

      setSelectedStrategy(strategyName);
      setConfig(prev => ({
        ...prev,
        strategy: strategyName,
        parameters: defaultParams
      }));
    }
  };

  const handleParameterChange = (paramName: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [paramName]: value
      }
    }));
  };

  const handleSymbolToggle = (symbol: string) => {
    setConfig(prev => ({
      ...prev,
      symbols: prev.symbols.includes(symbol)
        ? prev.symbols.filter(s => s !== symbol)
        : [...prev.symbols, symbol]
    }));
  };

  const runBacktest = async () => {
    if (!config.strategy || config.symbols.length === 0 || !config.startDate || !config.endDate) {
      alert('Please fill in all required fields');
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.post('/backtest/run', config);
      const backtestId = response.data.id;

      // Add to running backtests
      const newBacktest: BacktestResult = {
        id: backtestId,
        status: 'running',
        config: { ...config }
      };
      setRunningBacktests(prev => [...prev, newBacktest]);

      // Poll for completion
      pollBacktestStatus(backtestId);
    } catch (error) {
      console.error('Failed to start backtest:', error);
      alert('Failed to start backtest');
    } finally {
      setIsLoading(false);
    }
  };

  const pollBacktestStatus = (backtestId: string) => {
    const poll = async () => {
      try {
        const response = await api.get(`/backtest/status/${backtestId}`);
        const result: BacktestResult = response.data;

        if (result.status === 'completed' || result.status === 'failed') {
          // Move from running to completed
          setRunningBacktests(prev => prev.filter(b => b.id !== backtestId));
          setCompletedBacktests(prev => [result, ...prev]);
        } else {
          // Still running, continue polling
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('Failed to poll backtest status:', error);
        setTimeout(poll, 5000); // Retry with longer interval
      }
    };

    poll();
  };

  const selectedStrategyData = strategies.find(s => s.name === selectedStrategy);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Backtesting Platform</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Backtest Configuration</h2>

              {/* Strategy Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Strategy
                </label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => handleStrategyChange(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a strategy...</option>
                  {strategies.map(strategy => (
                    <option key={strategy.name} value={strategy.name}>
                      {strategy.name}
                    </option>
                  ))}
                </select>
                {selectedStrategyData && (
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedStrategyData.description}
                  </p>
                )}
              </div>

              {/* Strategy Parameters */}
              {selectedStrategyData && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parameters
                  </label>
                  <div className="space-y-3">
                    {selectedStrategyData.parameters.map(param => (
                      <div key={param.name}>
                        <label className="block text-xs text-gray-600 mb-1">
                          {param.name}
                        </label>
                        {param.type === 'number' && (
                          <input
                            type="number"
                            min={param.min}
                            max={param.max}
                            step={param.step}
                            value={config.parameters[param.name] || param.default}
                            onChange={(e) => handleParameterChange(param.name, parseFloat(e.target.value))}
                            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                          />
                        )}
                        {param.type === 'select' && param.options && (
                          <select
                            value={config.parameters[param.name] || param.default}
                            onChange={(e) => handleParameterChange(param.name, e.target.value)}
                            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                          >
                            {param.options.map(option => (
                              <option key={option} value={option}>{option}</option>
                            ))}
                          </select>
                        )}
                        {param.type === 'boolean' && (
                          <input
                            type="checkbox"
                            checked={config.parameters[param.name] || param.default}
                            onChange={(e) => handleParameterChange(param.name, e.target.checked)}
                            className="rounded"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Symbol Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Symbols ({config.symbols.length} selected)
                </label>
                <div className="max-h-32 overflow-y-auto border border-gray-300 rounded p-2">
                  {symbols.map(symbol => (
                    <label key={symbol} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={config.symbols.includes(symbol)}
                        onChange={() => handleSymbolToggle(symbol)}
                        className="rounded"
                      />
                      <span>{symbol}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Date Range */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date Range
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="date"
                    value={config.startDate}
                    onChange={(e) => setConfig(prev => ({ ...prev, startDate: e.target.value }))}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  />
                  <input
                    type="date"
                    value={config.endDate}
                    onChange={(e) => setConfig(prev => ({ ...prev, endDate: e.target.value }))}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  />
                </div>
              </div>

              {/* Run Button */}
              <button
                onClick={runBacktest}
                disabled={isLoading || !config.strategy || config.symbols.length === 0}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Running...' : 'Run Backtest'}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {/* Running Backtests */}
            {runningBacktests.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">Running Backtests</h2>
                <div className="space-y-3">
                  {runningBacktests.map(backtest => (
                    <div key={backtest.id} className="flex items-center justify-between p-3 bg-blue-50 rounded">
                      <div>
                        <div className="font-medium">{backtest.config.strategy}</div>
                        <div className="text-sm text-gray-600">
                          {backtest.config.symbols.join(', ')} • {backtest.config.startDate} to {backtest.config.endDate}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-sm text-blue-600">Running</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Completed Backtests */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Backtest Results</h2>
              {completedBacktests.length === 0 ? (
                <p className="text-gray-500">No completed backtests yet</p>
              ) : (
                <div className="space-y-3">
                  {completedBacktests.map(backtest => (
                    <div
                      key={backtest.id}
                      onClick={() => setSelectedResult(backtest)}
                      className="p-4 border border-gray-200 rounded cursor-pointer hover:bg-gray-50"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{backtest.config.strategy}</div>
                          <div className="text-sm text-gray-600">
                            {backtest.config.symbols.join(', ')} • {backtest.config.startDate} to {backtest.config.endDate}
                          </div>
                        </div>
                        {backtest.metrics && (
                          <div className="text-right">
                            <div className={`text-lg font-semibold ${backtest.metrics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {backtest.metrics.totalReturn.toFixed(2)}%
                            </div>
                            <div className="text-sm text-gray-600">
                              Sharpe: {backtest.metrics.sharpeRatio.toFixed(2)}
                            </div>
                          </div>
                        )}
                      </div>
                      {backtest.error && (
                        <div className="mt-2 text-sm text-red-600">
                          Error: {backtest.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Detailed Results Modal */}
        {selectedResult && selectedResult.metrics && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-start mb-6">
                  <h2 className="text-2xl font-bold">
                    {selectedResult.config.strategy} Results
                  </h2>
                  <button
                    onClick={() => setSelectedResult(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>

                {/* Metrics Overview */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">Total Return</div>
                    <div className={`text-xl font-semibold ${selectedResult.metrics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {selectedResult.metrics.totalReturn.toFixed(2)}%
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">Sharpe Ratio</div>
                    <div className="text-xl font-semibold">{selectedResult.metrics.sharpeRatio.toFixed(2)}</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">Win Rate</div>
                    <div className="text-xl font-semibold">{selectedResult.metrics.winRate.toFixed(1)}%</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">Total Trades</div>
                    <div className="text-xl font-semibold">{selectedResult.metrics.totalTrades}</div>
                  </div>
                </div>

                {/* Equity Curve */}
                {selectedResult.equityCurve && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3">Equity Curve</h3>
                    <div className="h-64 bg-gray-50 rounded p-4">
                      {/* Simple chart representation - in real app, use a charting library */}
                      <div className="flex items-end space-x-1 h-full">
                        {selectedResult.equityCurve.slice(-50).map((point, index) => (
                          <div
                            key={index}
                            className="bg-blue-500 flex-1 rounded-t"
                            style={{
                              height: `${Math.max(0, (point.equity / Math.max(...selectedResult.equityCurve!.map(p => p.equity))) * 100)}%`
                            }}
                            title={`${point.date}: ₹${point.equity.toLocaleString()}`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Recent Trades */}
                {selectedResult.trades && selectedResult.trades.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Recent Trades</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Symbol</th>
                            <th className="text-left p-2">Side</th>
                            <th className="text-right p-2">Quantity</th>
                            <th className="text-right p-2">Entry Price</th>
                            <th className="text-right p-2">Exit Price</th>
                            <th className="text-right p-2">P&L</th>
                            <th className="text-left p-2">Entry Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedResult.trades.slice(-10).map((trade, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2">{trade.symbol}</td>
                              <td className="p-2">{trade.side}</td>
                              <td className="p-2 text-right">{trade.quantity}</td>
                              <td className="p-2 text-right">₹{trade.entryPrice.toFixed(2)}</td>
                              <td className="p-2 text-right">₹{trade.exitPrice.toFixed(2)}</td>
                              <td className={`p-2 text-right ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                ₹{trade.pnl.toFixed(2)}
                              </td>
                              <td className="p-2">{new Date(trade.entryTime).toLocaleDateString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Backtesting;
