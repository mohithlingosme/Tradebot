import { useEffect, useState } from 'react';
import { socketService } from '../lib/socket';
import { useAuth } from './useAuth';

export const useMarketSocket = (symbol?: string) => {
  const [marketData, setMarketData] = useState<any>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (token && symbol) {
      socketService.connect(token);
      socketService.subscribeToMarketData(symbol, (data) => {
        setMarketData(data);
      });

      return () => {
        socketService.unsubscribeFromMarketData(symbol);
      };
    }
  }, [token, symbol]);

  return marketData;
};
