import traceback
import importlib

try:
    m = importlib.import_module('trading_engine')
    print('TradingMode=', getattr(m, 'TradingMode', None))
    print('LiveTradingEngine=', getattr(m, 'LiveTradingEngine', None))
    print('StrategyManager=', getattr(m, 'StrategyManager', None))
except Exception as e:
    traceback.print_exc()

# Additional check to import full module name directly
try:
    m2 = importlib.import_module('trading_engine.live_trading_engine')
    print('import trading_engine.live_trading_engine ok')
except Exception:
    traceback.print_exc()
