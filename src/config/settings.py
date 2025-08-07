"""
Settings configuration for Quote Master Pro
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from datetime import datetime

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Quote Master Pro"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "sqlite:///./quote_master_pro.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Services - Primary Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # AI Services - Azure (Optional)
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    
    # Email Configuration
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: str = "mp3,wav,m4a,flac,webm"
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ["mp3", "wav", "m4a", "ogg", "webm"]
    
    # Voice Processing
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # AI Service Configuration
    OPENAI_PRIORITY: int = 1
    ANTHROPIC_PRIORITY: int = 2
    AZURE_PRIORITY: int = 3
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_TOKENS_PER_REQUEST: int = 4000
    ENABLE_COST_TRACKING: bool = True
    MONTHLY_BUDGET_LIMIT: float = 500.00
    CACHE_TTL_SECONDS: int = 3600
    ENABLE_RESPONSE_CACHING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env

    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp as ISO string"""
        return datetime.utcnow().isoformat()

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings