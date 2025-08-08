"""Application configuration settings."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Quote Master Pro"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "your-secret-key-here"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str = "sqlite:///./quote_master_pro.db"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "quote_master_pro"
    db_user: str = "username"
    db_password: str = "password"
    db_pool_size: int = 20
    db_pool_overflow: int = 0

    # Redis (with memory cache fallback)
    redis_url: str = "memory://localhost"  # Default to memory cache for development
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AI Services
    openai_api_key: str = "your-openai-api-key"
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7

    anthropic_api_key: str = "your-anthropic-api-key"
    anthropic_model: str = "claude-3-sonnet-20240229"
    anthropic_max_tokens: int = 4000

    # Azure OpenAI
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment_name: str = "gpt-4"

    # AI Service Configuration
    ai_service_timeout: int = 30
    ai_service_max_retries: int = 3
    ai_service_cache_ttl: int = 3600
    ai_service_rate_limit_openai: int = 60
    ai_service_rate_limit_anthropic: int = 50
    ai_service_rate_limit_azure: int = 60

    # Voice Recognition
    whisper_model: str = "base"
    speech_recognition_timeout: int = 5
    audio_sample_rate: int = 16000

    # Security
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    bcrypt_rounds: int = 12

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # File Upload
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = [
        "audio/wav",
        "audio/mp3",
        "audio/mpeg",
        "audio/ogg",
    ]

    # Monitoring
    prometheus_port: int = 8001
    sentry_dsn: Optional[str] = None
    new_relic_license_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/app.log"

    # Cache
    cache_ttl: int = 3600
    cache_prefix: str = "quote_master_pro"

    # Email
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_user: str = "your-email@gmail.com"
    email_password: str = "your-app-password"
    email_from: str = "Quote Master Pro <noreply@quotemasterpro.com>"

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Analytics
    analytics_enabled: bool = True
    analytics_retention_days: int = 90

    # Feature Flags
    enable_voice_recognition: bool = True
    enable_ai_psychology: bool = True
    enable_analytics: bool = True
    enable_caching: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Allow extra fields from .env
    }

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v

    @field_validator("log_level")
    @classmethod
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

    # Uppercase aliases for AI service compatibility
    @property
    def OPENAI_API_KEY(self) -> str:
        """OpenAI API key (uppercase alias)."""
        return self.openai_api_key

    @property
    def ANTHROPIC_API_KEY(self) -> str:
        """Anthropic API key (uppercase alias)."""
        return self.anthropic_api_key

    @property
    def AZURE_OPENAI_API_KEY(self) -> Optional[str]:
        """Azure OpenAI API key (uppercase alias)."""
        return self.azure_openai_api_key

    @property
    def AZURE_OPENAI_ENDPOINT(self) -> Optional[str]:
        """Azure OpenAI endpoint (uppercase alias)."""
        return self.azure_openai_endpoint


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
