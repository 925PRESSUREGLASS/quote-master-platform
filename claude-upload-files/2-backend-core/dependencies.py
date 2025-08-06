"""Dependency injection for FastAPI routes."""

from typing import Optional, Generator
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import verify_token, SecurityException
from src.core.config import get_settings
from src.api.models.user import User
from src.api.models.analytics import UserSession

security = HTTPBearer()
settings = get_settings()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identification",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user
        
    except SecurityException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_current_premium_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """Get current premium user."""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None


class RateLimitChecker:
    """Rate limiting dependency."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
    
    def __call__(
        self,
        current_user: Optional[User] = Depends(get_optional_current_user)
    ):
        """Check rate limits."""
        # Implement rate limiting logic here
        # For now, just return True
        return True


class QuotaChecker:
    """Quota checking dependency."""
    
    def __init__(self, quota_type: str):
        self.quota_type = quota_type
    
    def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        """Check user quotas."""
        # Implement quota checking logic
        # For example, check daily quote generation limits
        if self.quota_type == "quotes":
            # Check if user has exceeded daily quote limit
            if not current_user.is_premium and current_user.api_calls_today >= 50:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Daily quote generation limit exceeded. Upgrade to premium for unlimited quotes."
                )
        
        return True


def get_user_session(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Optional[UserSession]:
    """Get or create user session."""
    if not current_user:
        return None
    
    # Get or create active session
    session = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).first()
    
    if not session:
        # Create new session
        session = UserSession(
            user_id=current_user.id,
            session_token=f"session_{current_user.id}_{datetime.utcnow().timestamp()}"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session


# Pre-configured dependencies
check_quote_quota = QuotaChecker("quotes")
check_voice_quota = QuotaChecker("voice")
check_api_rate_limit = RateLimitChecker(60)  # 60 requests per minute