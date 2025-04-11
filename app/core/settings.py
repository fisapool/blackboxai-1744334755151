from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Application Settings
    APP_ENV: str = "production"
    DEBUG: bool = False
    APP_TITLE: str = "HR Analytics Dashboard"
    APP_VERSION: str = "1.0.0"
    
    # Security Settings
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # Database Settings
    DATABASE_URL: str
    REDIS_URL: str
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Rate Limiting
    RATE_LIMIT_PER_SECOND: int = 10
    
    class Config:
        env_file = ".env.prod"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
