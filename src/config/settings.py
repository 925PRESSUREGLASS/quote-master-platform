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
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./quote_master_pro.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_AUDIO_EXTENSIONS: List[str] = ["mp3", "wav", "m4a", "ogg", "webm"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

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