from decimal import Decimal
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")

    # JWT Configuration
    jwt_secret_key: str = Field(default="test-secret-key-for-jwt", env="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(default="test-refresh-secret-key-for-jwt", env="JWT_REFRESH_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # Security
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")

    # Rate Limiting
    rate_limit_requests: int = Field(default=5, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_minutes: int = Field(default=1, env="RATE_LIMIT_WINDOW_MINUTES")

    # Email (for future verification)
    smtp_server: str = Field(default="", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")

    # Redis (for rate limiting and sessions)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Paper Trading Configuration
    execution_mode: str = Field(default="paper", env="EXECUTION_MODE")
    paper_starting_cash: Decimal = Field(default=Decimal("100000"), env="PAPER_STARTING_CASH")
    slippage_bps: int = Field(default=5, env="SLIPPAGE_BPS")
    brokerage_flat: int = Field(default=0, env="BROKERAGE_FLAT")
    brokerage_bps: int = Field(default=0, env="BROKERAGE_BPS")
    paper_enforce_market_hours: bool = Field(default=False, env="PAPER_ENFORCE_MARKET_HOURS")

    # Risk Enforcement Configuration
    enable_risk_enforcement: bool = Field(default=True, env="ENABLE_RISK_ENFORCEMENT")
    enable_force_square_off: bool = Field(default=False, env="ENABLE_FORCE_SQUARE_OFF")
    max_daily_loss_inr: Decimal = Field(default=Decimal("2000"), env="MAX_DAILY_LOSS_INR")
    max_daily_loss_pct: Decimal = Field(default=Decimal("0"), env="MAX_DAILY_LOSS_PCT")
    max_position_value_inr: Decimal = Field(default=Decimal("25000"), env="MAX_POSITION_VALUE_INR")
    max_position_qty: Decimal = Field(default=Decimal("200"), env="MAX_POSITION_QTY")
    max_gross_exposure_inr: Decimal = Field(default=Decimal("75000"), env="MAX_GROSS_EXPOSURE_INR")
    max_net_exposure_inr: Decimal = Field(default=Decimal("75000"), env="MAX_NET_EXPOSURE_INR")
    max_open_orders: int = Field(default=20, env="MAX_OPEN_ORDERS")
    cutoff_time: str = Field(default="15:15", env="CUTOFF_TIME")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
