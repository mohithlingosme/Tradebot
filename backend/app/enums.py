from enum import Enum

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class RiskEventType(str, Enum):
    REJECT = "REJECT"
    KILL_SWITCH = "KILL_SWITCH"
    LIMIT_BREACH = "LIMIT_BREACH"

class EngineEventLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

class EngineEventComponent(str, Enum):
    ENGINE = "engine"
    API = "api"
    RISK = "risk"
    EXECUTION = "execution"
    INGESTION = "ingestion"
