"""Authentication router for Quote Master Pro."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_active_user, get_current_user
from src.api.models.user import User
from src.api.schemas.user import (
    EmailVerificationConfirm,
    EmailVerificationRequest,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from src.core.config import get_settings
from src.core.database import get_db
from src.core.security import (
    create_access_token,
    create_refresh_token,
    generate_reset_token,
    get_password_hash,
    verify_password,
    verify_token,
)

router = APIRouter()
settings = get_settings()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        # Match tests expecting 400 and message containing 'email already registered'
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Check username if provided
    if user_data.username:
        existing_username = (
            db.query(User).filter(User.username == user_data.username).first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)

    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        bio=user_data.bio,
        hashed_password=hashed_password,
        timezone=user_data.timezone,
        language=user_data.language,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # TODO: Send verification email

    return db_user


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""

    # Get user by email
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated",
        )

    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)

    if login_data.remember_me:
        # Extend token expiry for "remember me"
        access_token_expires = timedelta(days=7)
        refresh_token_expires = timedelta(days=30)

    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires
    )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""

    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            expires_in=int(access_token_expires.total_seconds()),
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (invalidate tokens - client-side implementation)."""

    # In a real implementation, you might want to:
    # 1. Blacklist the tokens in Redis
    # 2. Clear user sessions
    # 3. Log the logout event

    return {"message": "Successfully logged out"}


@router.post("/password/reset-request")
async def request_password_reset(
    reset_data: PasswordResetRequest, db: Session = Depends(get_db)
):
    """Request password reset token."""

    user = db.query(User).filter(User.email == reset_data.email).first()

    if user:
        # Generate reset token
        reset_token = generate_reset_token()

        # TODO: Store reset token in database/cache with expiry
        # TODO: Send password reset email

        # For demo purposes, return the token (DON'T DO THIS IN PRODUCTION!)
        if settings.is_development:
            return {"message": "Password reset email sent", "reset_token": reset_token}

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password/reset-confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """Confirm password reset with token."""

    # TODO: Verify reset token from database/cache
    # For demo purposes, we'll skip token verification

    # In a real implementation:
    # 1. Verify the reset token
    # 2. Check if it's not expired
    # 3. Get the associated user

    # For now, just return success
    return {"message": "Password has been reset successfully"}


@router.post("/password/change")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change user password."""

    # Verify current password
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/email/verify-request")
async def request_email_verification(
    verification_data: EmailVerificationRequest, db: Session = Depends(get_db)
):
    """Request email verification."""

    user = db.query(User).filter(User.email == verification_data.email).first()

    if user and not user.is_verified:
        # TODO: Generate and send verification email
        pass

    return {
        "message": "If the email exists and is unverified, a verification link has been sent"
    }


@router.post("/email/verify-confirm")
async def confirm_email_verification(
    verification_data: EmailVerificationConfirm, db: Session = Depends(get_db)
):
    """Confirm email verification with token."""

    # TODO: Verify the verification token
    # For demo purposes, we'll skip token verification

    return {"message": "Email verified successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/validate-token")
async def validate_token(current_user: User = Depends(get_current_user)):
    """Validate current token."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "role": current_user.role,
    }
