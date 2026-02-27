from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ANZA FNO Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # AngelOne
    ANGEL_API_KEY: Optional[str] = None
    ANGEL_CLIENT_ID: Optional[str] = None
    ANGEL_PASSWORD: Optional[str] = None
    ANGEL_TOTP_KEY: Optional[str] = None

    # OpenAlgo
    OPENALGO_API_KEY: Optional[str] = None
    OPENALGO_HOST: Optional[str] = None

    # Intervals
    MARKET_DATA_INTERVAL: int = 60
    OI_ANALYSIS_INTERVAL: int = 180

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
