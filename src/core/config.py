"""Application configuration settings."""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = Field(default="Quote Master Pro", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="quote_master_pro", env="DB_NAME")
    db_user: str = Field(default="username", env="DB_USER")
    db_password: str = Field(default="password", env="DB_PASSWORD")
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_pool_overflow: int = Field(default=0, env="DB_POOL_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # AI Services
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(default=4000, env="ANTHROPIC_MAX_TOKENS")
    
    # Voice Recognition
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    speech_recognition_timeout: int = Field(default=5, env="SPEECH_RECOGNITION_TIMEOUT")
    audio_sample_rate: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    
    # Security
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    allowed_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="ALLOWED_METHODS"
    )
    allowed_headers: List[str] = Field(default=["*"], env="ALLOWED_HEADERS")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # File Upload
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=["audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Monitoring
    prometheus_port: int = Field(default=8001, env="PROMETHEUS_PORT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    new_relic_license_key: Optional[str] = Field(default=None, env="NEW_RELIC_LICENSE_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # Cache
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_prefix: str = Field(default="quote_master_pro", env="CACHE_PREFIX")
    
    # Email
    email_host: str = Field(default="smtp.gmail.com", env="EMAIL_HOST")
    email_port: int = Field(default=587, env="EMAIL_PORT")
    email_user: str = Field(default="your-email@gmail.com", env="EMAIL_USER")
    email_password: str = Field(default="your-app-password", env="EMAIL_PASSWORD")
    email_from: str = Field(
        default="Quote Master Pro <noreply@quotemasterpro.com>",
        env="EMAIL_FROM"
    )
    
    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # Analytics
    analytics_enabled: bool = Field(default=True, env="ANALYTICS_ENABLED")
    analytics_retention_days: int = Field(default=90, env="ANALYTICS_RETENTION_DAYS")
    
    # Feature Flags
    enable_voice_recognition: bool = Field(default=True, env="ENABLE_VOICE_RECOGNITION")
    enable_ai_psychology: bool = Field(default=True, env="ENABLE_AI_PSYCHOLOGY")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level setting."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    @property
    def database_config(self) -> dict:
        """Get database configuration dictionary."""
        return {
            "url": self.database_url,
            "pool_size": self.db_pool_size,
            "pool_overflow": self.db_pool_overflow,
            "echo": self.debug and self.is_development,
        }
    
    @property
    def redis_config(self) -> dict:
        """Get Redis configuration dictionary."""
        return {
            "host": self.redis_host,
            "port": self.redis_port,
            "db": self.redis_db,
            "password": self.redis_password,
            "decode_responses": True,
        }
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()