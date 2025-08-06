"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, Union, Any
import secrets

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt

from .config import get_settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()

# Get settings
settings = get_settings()


class SecurityException(HTTPException):
    """Custom security exception."""
    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            raise SecurityException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        raise SecurityException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract current user ID from JWT token."""
    try:
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise SecurityException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identification",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user_id
        
    except JWTError:
        raise SecurityException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    """Generate a password reset token."""
    return secrets.token_urlsafe(16)


class RoleChecker:
    """Role-based access control."""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user_data: dict = Depends(get_current_user_id)):
        """Check if user has required role."""
        # In a real implementation, you would fetch user data from database
        # This is a simplified version
        user_role = user_data.get("role", "user")
        
        if user_role not in self.allowed_roles:
            raise SecurityException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return user_data


# Pre-configured role checkers
require_admin = RoleChecker(["admin"])
require_moderator = RoleChecker(["admin", "moderator"])
require_premium = RoleChecker(["admin", "moderator", "premium"])


def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special


def create_password_reset_data(user_id: str, email: str) -> dict:
    """Create password reset token data."""
    reset_token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    
    return {
        "token": reset_token,
        "user_id": user_id,
        "email": email,
        "expires_at": expires_at,
        "used": False
    }


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return get_password_hash(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify API key against stored hash."""
    return verify_password(api_key, hashed_key)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(
        self,
        key: str,
        limit: int = None,
        window: int = None
    ) -> bool:
        """Check if request is within rate limit."""
        limit = limit or settings.rate_limit_requests
        window = window or settings.rate_limit_window
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()