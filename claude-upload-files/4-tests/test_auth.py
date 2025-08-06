"""
Unit tests for authentication service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.auth import AuthService
from src.core.exceptions import AuthenticationError, ValidationError


class TestAuthService:
    """Test authentication service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auth_service = AuthService()

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = self.auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")

    def test_verify_password(self):
        """Test password verification."""
        password = "testpassword123"
        hashed = self.auth_service.hash_password(password)
        
        # Correct password should verify
        assert self.auth_service.verify_password(password, hashed) is True
        
        # Incorrect password should not verify
        assert self.auth_service.verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = self.auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should contain encoded data
        from jwt import decode
        decoded = decode(
            token, 
            self.auth_service.secret_key, 
            algorithms=[self.auth_service.algorithm]
        )
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded

    def test_create_access_token_with_expiration(self):
        """Test access token creation with custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=15)
        token = self.auth_service.create_access_token(data, expires_delta)
        
        from jwt import decode
        decoded = decode(
            token, 
            self.auth_service.secret_key, 
            algorithms=[self.auth_service.algorithm]
        )
        
        # Check expiration is approximately 15 minutes from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        assert abs((exp_time - expected_exp).total_seconds()) < 60

    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = self.auth_service.create_access_token(data)
        
        payload = self.auth_service.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

    def test_verify_token_expired(self):
        """Test token verification with expired token."""
        data = {"sub": "user123"}
        expired_token = self.auth_service.create_access_token(
            data, expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(AuthenticationError):
            self.auth_service.verify_token(expired_token)

    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(AuthenticationError):
            self.auth_service.verify_token(invalid_token)

    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid passwords."""
        valid_passwords = [
            "strongPassword123",
            "P@ssw0rd!",
            "MySecure123",
            "ComplexPass1!",
        ]
        
        for password in valid_passwords:
            # Should not raise an exception
            self.auth_service.validate_password_strength(password)

    def test_validate_password_strength_invalid(self):
        """Test password strength validation with invalid passwords."""
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoNumbers",  # No numbers
            "password",  # Too common
            "12345678",  # Too simple
        ]
        
        for password in invalid_passwords:
            with pytest.raises(ValidationError):
                self.auth_service.validate_password_strength(password)

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "firstname+lastname@company.org",
            "admin@subdomain.example.com",
        ]
        
        for email in valid_emails:
            # Should not raise an exception
            self.auth_service.validate_email(email)

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "notanemail",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@domain",
            "",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                self.auth_service.validate_email(email)

    @patch('src.services.auth.secrets.token_urlsafe')
    def test_generate_reset_token(self, mock_token):
        """Test password reset token generation."""
        mock_token.return_value = "random_token_123"
        
        token = self.auth_service.generate_reset_token()
        assert token == "random_token_123"
        mock_token.assert_called_once_with(32)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123"}
        token = self.auth_service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        from jwt import decode
        decoded = decode(
            token, 
            self.auth_service.secret_key, 
            algorithms=[self.auth_service.algorithm]
        )
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"