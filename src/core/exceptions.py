"""Custom exceptions for the Quote Master Pro application."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class QuoteMasterProException(Exception):
    """Base exception for Quote Master Pro."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class DatabaseException(QuoteMasterProException):
    """Database-related exceptions."""
    pass


class AuthenticationException(HTTPException):
    """Authentication-related exceptions."""
    
    def __init__(
        self,
        detail: str = "Authentication failed",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(HTTPException):
    """Authorization-related exceptions."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationException(HTTPException):
    """Validation-related exceptions."""
    
    def __init__(
        self,
        detail: str = "Validation failed",
        errors: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
        self.errors = errors or {}


class NotFoundHttpException(HTTPException):
    """Resource not found exceptions."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ConflictException(HTTPException):
    """Resource conflict exceptions."""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class RateLimitException(HTTPException):
    """Rate limit exceeded exceptions."""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers
        )


class ServiceUnavailableException(HTTPException):
    """Service unavailable exceptions."""
    
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


# AI Service Exceptions
class AIServiceException(QuoteMasterProException):
    """Base AI service exception."""
    pass


class OpenAIException(AIServiceException):
    """OpenAI service exceptions."""
    pass


class AnthropicException(AIServiceException):
    """Anthropic service exceptions."""
    pass


class VoiceProcessingException(QuoteMasterProException):
    """Voice processing exceptions."""
    pass


class WhisperException(VoiceProcessingException):
    """Whisper AI exceptions."""
    pass


class SpeechRecognitionException(VoiceProcessingException):
    """Speech recognition exceptions."""
    pass


# Quote Engine Exceptions
class QuoteGenerationException(QuoteMasterProException):
    """Quote generation exceptions."""
    pass


class PsychologyAnalysisException(QuoteMasterProException):
    """Psychology analysis exceptions."""
    pass


# Analytics Exceptions
class AnalyticsException(QuoteMasterProException):
    """Analytics processing exceptions."""
    pass


# Cache Exceptions
class CacheException(QuoteMasterProException):
    """Cache-related exceptions."""
    pass


class RedisException(CacheException):
    """Redis cache exceptions."""
    pass


# File Processing Exceptions
class FileProcessingException(QuoteMasterProException):
    """File processing exceptions."""
    pass


class InvalidFileTypeException(FileProcessingException):
    """Invalid file type exceptions."""
    pass


class FileSizeException(FileProcessingException):
    """File size limit exceptions."""
    pass


# User Management Exceptions
class UserException(QuoteMasterProException):
    """User management exceptions."""
    pass


class UserNotFoundHttpException(NotFoundHttpException):
    """User not found exceptions."""
    
    def __init__(self, user_id: str = None):
        detail = "User not found"
        if user_id:
            detail += f" (ID: {user_id})"
        super().__init__(detail=detail)


class UserAlreadyExistsException(ConflictException):
    """User already exists exceptions."""
    
    def __init__(self, email: str = None):
        detail = "User already exists"
        if email:
            detail += f" (Email: {email})"
        super().__init__(detail=detail)


class InvalidCredentialsException(AuthenticationException):
    """Invalid credentials exceptions."""
    
    def __init__(self):
        super().__init__(detail="Invalid email or password")


class EmailNotVerifiedException(AuthenticationException):
    """Email not verified exceptions."""
    
    def __init__(self):
        super().__init__(detail="Email address not verified")


class AccountDisabledException(AuthenticationException):
    """Account disabled exceptions."""
    
    def __init__(self):
        super().__init__(detail="Account has been disabled")


# Configuration Exceptions
class ConfigurationException(QuoteMasterProException):
    """Configuration-related exceptions."""
    pass


class MissingConfigurationException(ConfigurationException):
    """Missing configuration exceptions."""
    
    def __init__(self, config_key: str):
        super().__init__(
            message=f"Missing required configuration: {config_key}",
            error_code="MISSING_CONFIG"
        )


# External Service Exceptions
class ExternalServiceException(QuoteMasterProException):
    """External service exceptions."""
    pass


class ThirdPartyAPIException(ExternalServiceException):
    """Third-party API exceptions."""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: Optional[int] = None
    ):
        super().__init__(
            message=f"{service_name} API error: {message}",
            details={"service": service_name, "status_code": status_code},
            error_code="THIRD_PARTY_API_ERROR"
        )


# Background Task Exceptions
class BackgroundTaskException(QuoteMasterProException):
    """Background task exceptions."""
    pass


class CeleryTaskException(BackgroundTaskException):
    """Celery task exceptions."""
    pass


# Monitoring Exceptions
class MonitoringException(QuoteMasterProException):
    """Monitoring and metrics exceptions."""
    pass


class MetricsCollectionException(MonitoringException):
    """Metrics collection exceptions."""
    pass


# Business Logic Exceptions
class BusinessLogicException(QuoteMasterProException):
    """Business logic exceptions."""
    pass


class QuotaExceededException(BusinessLogicException):
    """Quota exceeded exceptions."""
    
    def __init__(self, quota_type: str, limit: int):
        super().__init__(
            message=f"{quota_type} quota exceeded (limit: {limit})",
            details={"quota_type": quota_type, "limit": limit},
            error_code="QUOTA_EXCEEDED"
        )


class FeatureNotAvailableException(BusinessLogicException):
    """Feature not available exceptions."""
    
    def __init__(self, feature_name: str):
        super().__init__(
            message=f"Feature not available: {feature_name}",
            details={"feature": feature_name},
            error_code="FEATURE_NOT_AVAILABLE"
        )


class MaintenanceModeException(ServiceUnavailableException):
    """Maintenance mode exceptions."""
    
    def __init__(self, message: str = "System is under maintenance"):
        super().__init__(detail=message)


# Utility function to convert internal exceptions to HTTP exceptions
def convert_to_http_exception(
    exc: QuoteMasterProException,
    default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> HTTPException:
    """Convert internal exception to HTTP exception."""
    
    # Map specific exceptions to HTTP status codes
    status_map = {
        UserNotFoundHttpException: status.HTTP_404_NOT_FOUND,
        UserAlreadyExistsException: status.HTTP_409_CONFLICT,
        AuthenticationException: status.HTTP_401_UNAUTHORIZED,
        AuthorizationException: status.HTTP_403_FORBIDDEN,
        ValidationException: status.HTTP_422_UNPROCESSABLE_ENTITY,
        RateLimitException: status.HTTP_429_TOO_MANY_REQUESTS,
        ServiceUnavailableException: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    
    status_code = status_map.get(type(exc), default_status_code)
    
    detail = exc.message if hasattr(exc, 'message') else str(exc)
    
    return HTTPException(
        status_code=status_code,
        detail=detail
    )