"""
Pytest configuration and fixtures for Quote Master Pro tests.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from src.core.database import get_db, Base
from src.core.config import get_settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/quote_master_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_session: AsyncSession):
    """Override the get_db dependency."""
    async def _override_get_db():
        yield test_session
    
    return _override_get_db


@pytest.fixture
def test_client(override_get_db) -> TestClient:
    """Create test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ.update({
        "ENVIRONMENT": "test",
        "DATABASE_URL": TEST_DATABASE_URL,
        "JWT_SECRET_KEY": "test-secret-key",
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "REDIS_URL": "redis://localhost:6379/15",  # Use database 15 for tests
    })
    
    yield get_settings()
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpassword123",
    }


@pytest.fixture
def mock_quote_data():
    """Mock quote data for testing."""
    return {
        "text": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs",
        "category": "motivation",
        "context": "Career advice",
    }


@pytest.fixture
def mock_voice_data():
    """Mock voice recording data for testing."""
    return {
        "filename": "test_recording.wav",
        "duration_seconds": 30.5,
        "file_size": 1024000,
        "file_format": "wav",
        "transcription": "This is a test transcription",
    }


@pytest.fixture
async def authenticated_user(test_session: AsyncSession, mock_user_data):
    """Create and return an authenticated user."""
    from src.services.auth import AuthService
    from src.models.user import User
    
    auth_service = AuthService()
    
    # Create user
    user = User(
        email=mock_user_data["email"],
        username=mock_user_data["username"],
        full_name=mock_user_data["full_name"],
        password_hash=auth_service.hash_password(mock_user_data["password"]),
        is_verified=True,
        is_active=True,
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(authenticated_user):
    """Create authentication headers for testing."""
    from src.services.auth import AuthService
    
    auth_service = AuthService()
    access_token = auth_service.create_access_token(
        data={"sub": str(authenticated_user.id)}
    )
    
    return {"Authorization": f"Bearer {access_token}"}


# Async fixtures
@pytest_asyncio.fixture
async def async_test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add database marker for tests that use database fixtures
        if any(fixture in item.fixturenames for fixture in ["test_session", "async_test_session", "authenticated_user"]):
            item.add_marker(pytest.mark.database)
        
        # Add API marker for tests that use client fixtures
        if any(fixture in item.fixturenames for fixture in ["test_client", "async_client"]):
            item.add_marker(pytest.mark.api)