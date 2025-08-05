"""
Integration tests for quotes API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch


class TestQuotesAPI:
    """Test quotes API integration."""

    @pytest.mark.asyncio
    async def test_generate_quote_success(self, async_client: AsyncClient, auth_headers):
        """Test successful quote generation."""
        quote_request = {
            "prompt": "Generate a motivational quote about success",
            "category": "motivation",
            "style": "inspirational",
            "length": "medium"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "author": "Winston Churchill",
                "quality_score": 8.5,
                "category": "motivation"
            }
            
            response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["text"] == "Success is not final, failure is not fatal: it is the courage to continue that counts."
            assert data["author"] == "Winston Churchill"
            assert data["quality_score"] == 8.5

    @pytest.mark.asyncio
    async def test_generate_quote_unauthorized(self, async_client: AsyncClient):
        """Test quote generation without authentication."""
        quote_request = {
            "prompt": "Generate a quote",
            "category": "motivation"
        }
        
        response = await async_client.post("/api/quotes/generate", json=quote_request)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_user_quotes(self, async_client: AsyncClient, auth_headers):
        """Test getting user's quotes."""
        response = await async_client.get("/api/quotes/my-quotes", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_quote_by_id(self, async_client: AsyncClient, auth_headers):
        """Test getting a specific quote by ID."""
        # First create a quote
        quote_request = {
            "prompt": "Test quote",
            "category": "test"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "This is a test quote.",
                "author": "Test Author",
                "quality_score": 7.0,
                "category": "test"
            }
            
            create_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            quote_id = create_response.json()["id"]
            
            # Now get the quote by ID
            response = await async_client.get(f"/api/quotes/{quote_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == quote_id
            assert data["text"] == "This is a test quote."

    @pytest.mark.asyncio
    async def test_get_nonexistent_quote(self, async_client: AsyncClient, auth_headers):
        """Test getting a non-existent quote."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await async_client.get(f"/api/quotes/{fake_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_quote(self, async_client: AsyncClient, auth_headers):
        """Test updating a quote."""
        # First create a quote
        quote_request = {
            "prompt": "Original quote",
            "category": "test"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Original quote text.",
                "author": "Original Author",
                "quality_score": 7.0,
                "category": "test"
            }
            
            create_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            quote_id = create_response.json()["id"]
            
            # Update the quote
            update_data = {
                "text": "Updated quote text.",
                "author": "Updated Author"
            }
            
            response = await async_client.put(
                f"/api/quotes/{quote_id}", 
                json=update_data, 
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["text"] == "Updated quote text."
            assert data["author"] == "Updated Author"

    @pytest.mark.asyncio
    async def test_delete_quote(self, async_client: AsyncClient, auth_headers):
        """Test deleting a quote."""
        # First create a quote
        quote_request = {
            "prompt": "Quote to delete",
            "category": "test"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Quote to be deleted.",
                "author": "Test Author",
                "quality_score": 7.0,
                "category": "test"
            }
            
            create_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            quote_id = create_response.json()["id"]
            
            # Delete the quote
            response = await async_client.delete(f"/api/quotes/{quote_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
            
            # Verify it's deleted
            get_response = await async_client.get(f"/api/quotes/{quote_id}", headers=auth_headers)
            assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_like_quote(self, async_client: AsyncClient, auth_headers):
        """Test liking a quote."""
        # First create a quote
        quote_request = {
            "prompt": "Quote to like",
            "category": "test"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Likeable quote.",
                "author": "Test Author",
                "quality_score": 7.0,
                "category": "test"
            }
            
            create_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            quote_id = create_response.json()["id"]
            
            # Like the quote
            response = await async_client.post(f"/api/quotes/{quote_id}/like", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["liked"] is True
            assert data["like_count"] >= 1

    @pytest.mark.asyncio
    async def test_search_quotes(self, async_client: AsyncClient, auth_headers):
        """Test searching quotes."""
        search_params = {
            "q": "success",
            "category": "motivation",
            "limit": 10
        }
        
        response = await async_client.get(
            "/api/quotes/search", 
            params=search_params, 
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_quote_categories(self, async_client: AsyncClient):
        """Test getting available quote categories."""
        response = await async_client.get("/api/quotes/categories")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check category structure
        if data:
            category = data[0]
            assert "name" in category
            assert "slug" in category

    @pytest.mark.asyncio
    async def test_generate_quote_variations(self, async_client: AsyncClient, auth_headers):
        """Test generating quote variations."""
        # First create a quote
        quote_request = {
            "prompt": "Base quote for variations",
            "category": "test"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Original quote for variations.",
                "author": "Test Author",
                "quality_score": 7.0,
                "category": "test"
            }
            
            create_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            quote_id = create_response.json()["id"]
            
            # Generate variations
            with patch('src.services.quote.engine.QuoteEngine.generate_variations') as mock_variations:
                mock_variations.return_value = [
                    "First variation of the quote.",
                    "Second variation of the quote.",
                    "Third variation of the quote."
                ]
                
                response = await async_client.post(
                    f"/api/quotes/{quote_id}/variations", 
                    json={"count": 3}, 
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "variations" in data
                assert len(data["variations"]) == 3