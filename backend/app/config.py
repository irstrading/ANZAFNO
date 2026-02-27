# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "ANZA FNO Intelligence Platform"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "anza_secret_key_change_in_prod"

    # AngelOne API
    ANGELONE_API_KEY: str
    ANGELONE_CLIENT_ID: str
    ANGELONE_PASSWORD: str
    ANGELONE_TOTP_SECRET: str
    ANGELONE_FEED_TOKEN: Optional[str] = None

    # Database (TimescaleDB + Redis)
    DATABASE_URL: str = "postgresql://postgres:anza123@localhost:5432/anza_fno"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[int] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
