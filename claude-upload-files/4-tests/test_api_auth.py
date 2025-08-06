"""
Integration tests for authentication API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from tests.conftest import TestClient


class TestAuthenticationAPI:
    """Test authentication API integration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }
        
        response = await async_client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, async_client: AsyncClient, mock_user_data):
        """Test registration with duplicate email."""
        # Register first user
        await async_client.post("/api/auth/register", json=mock_user_data)
        
        # Try to register with same email
        duplicate_data = mock_user_data.copy()
        duplicate_data["username"] = "different_username"
        
        response = await async_client.post("/api/auth/register", json=duplicate_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, authenticated_user):
        """Test successful login."""
        login_data = {
            "email": authenticated_user.email,
            "password": "testpassword123"  # From mock_user_data
        }
        
        response = await async_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == str(authenticated_user.id)

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient, authenticated_user):
        """Test login with invalid credentials."""
        login_data = {
            "email": authenticated_user.email,
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = await async_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, auth_headers):
        """Test getting current user information."""
        response = await async_client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_token(self, async_client: AsyncClient, authenticated_user):
        """Test token refresh."""
        # First login to get tokens
        login_data = {
            "email": authenticated_user.email,
            "password": "testpassword123"
        }
        
        login_response = await async_client.post("/api/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Use refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = await async_client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]

    @pytest.mark.asyncio
    async def test_logout(self, async_client: AsyncClient, auth_headers):
        """Test user logout."""
        response = await async_client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert "successfully logged out" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password(self, async_client: AsyncClient, auth_headers):
        """Test password change."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }
        
        response = await async_client.post(
            "/api/auth/password/change", 
            json=password_data, 
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "password changed" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, async_client: AsyncClient, auth_headers):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456"
        }
        
        response = await async_client.post(
            "/api/auth/password/change", 
            json=password_data, 
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_request_password_reset(self, async_client: AsyncClient, authenticated_user):
        """Test password reset request."""
        reset_data = {"email": authenticated_user.email}
        
        response = await async_client.post("/api/auth/password/reset-request", json=reset_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "reset link sent" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_token_valid(self, async_client: AsyncClient, auth_headers):
        """Test token validation with valid token."""
        response = await async_client.post("/api/auth/validate-token", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, async_client: AsyncClient):
        """Test token validation with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.post("/api/auth/validate-token", headers=invalid_headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED