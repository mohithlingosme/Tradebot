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
    ALLOW_REDUCED = "ALLOW_REDUCED"
    HALT = "HALT"
    SQUAREOFF = "SQUAREOFF"
    RESUME = "RESUME"


class RiskAction(str, Enum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"
    REDUCE_QTY = "REDUCE_QTY"
    HALT_TRADING = "HALT_TRADING"
    FORCE_SQUARE_OFF = "FORCE_SQUARE_OFF"

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

class ProductType(str, Enum):
    MIS = "MIS"
    CNC = "CNC"
