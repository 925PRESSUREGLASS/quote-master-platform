"""
End-to-end tests for complete user journeys.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch


class TestUserJourney:
    """Test complete user journeys through the application."""

    @pytest.mark.asyncio
    async def test_complete_user_registration_and_quote_generation(self, async_client: AsyncClient):
        """Test complete user journey from registration to quote generation."""
        # Step 1: Register a new user
        user_data = {
            "email": "journey@example.com",
            "username": "journeyuser",
            "full_name": "Journey User",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }
        
        register_response = await async_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]
        
        # Step 2: Login with the new user
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = await async_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        tokens = login_response.json()
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Step 3: Generate a quote
        quote_request = {
            "prompt": "Generate an inspiring quote about perseverance",
            "category": "motivation",
            "style": "inspirational",
            "length": "medium"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Perseverance is not a long race; it is many short races one after the other.",
                "author": "Walter Elliot",
                "quality_score": 8.7,
                "category": "motivation"
            }
            
            quote_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            assert quote_response.status_code == status.HTTP_201_CREATED
            quote_data = quote_response.json()
            quote_id = quote_data["id"]
            
            # Verify quote was created
            assert quote_data["text"] == "Perseverance is not a long race; it is many short races one after the other."
            assert quote_data["user_id"] == user_id
        
        # Step 4: Retrieve user's quotes
        my_quotes_response = await async_client.get("/api/quotes/my-quotes", headers=auth_headers)
        assert my_quotes_response.status_code == status.HTTP_200_OK
        
        my_quotes_data = my_quotes_response.json()
        assert my_quotes_data["total"] >= 1
        assert any(q["id"] == quote_id for q in my_quotes_data["items"])
        
        # Step 5: Like the quote
        like_response = await async_client.post(f"/api/quotes/{quote_id}/like", headers=auth_headers)
        assert like_response.status_code == status.HTTP_200_OK
        assert like_response.json()["liked"] is True
        
        # Step 6: Update user profile
        profile_update = {
            "full_name": "Journey User Updated",
            "bio": "A user on a testing journey"
        }
        
        profile_response = await async_client.put("/api/users/me", json=profile_update, headers=auth_headers)
        assert profile_response.status_code == status.HTTP_200_OK
        assert profile_response.json()["full_name"] == "Journey User Updated"
        
        # Step 7: Logout
        logout_response = await async_client.post("/api/auth/logout", headers=auth_headers)
        assert logout_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_voice_to_quote_journey(self, async_client: AsyncClient, auth_headers):
        """Test journey from voice recording to quote generation."""
        # Step 1: Upload a voice recording
        voice_data = {
            "filename": "test_voice.wav",
            "duration_seconds": 45.0,
            "file_size": 2048000,
            "file_format": "wav"
        }
        
        with patch('src.services.voice.processor.VoiceProcessor.process_audio') as mock_process:
            mock_process.return_value = {
                "transcription": "Success comes to those who are willing to work hard and never give up on their dreams.",
                "confidence": 0.95,
                "language": "en",
                "sentiment": "positive"
            }
            
            upload_response = await async_client.post(
                "/api/voice/upload", 
                json=voice_data, 
                headers=auth_headers
            )
            
            assert upload_response.status_code == status.HTTP_201_CREATED
            recording_data = upload_response.json()
            recording_id = recording_data["id"]
        
        # Step 2: Process the voice recording
        with patch('src.services.voice.processor.VoiceProcessor.generate_quotes_from_transcription') as mock_quotes:
            mock_quotes.return_value = [
                {
                    "text": "Success comes to those who work hard and never give up.",
                    "author": "Generated from Voice",
                    "quality_score": 8.2,
                    "category": "motivation"
                }
            ]
            
            process_response = await async_client.post(
                f"/api/voice/{recording_id}/process", 
                headers=auth_headers
            )
            
            assert process_response.status_code == status.HTTP_200_OK
            quotes_data = process_response.json()
            assert len(quotes_data["quotes"]) >= 1
        
        # Step 3: Retrieve voice history
        history_response = await async_client.get("/api/voice/history", headers=auth_headers)
        assert history_response.status_code == status.HTTP_200_OK
        
        history_data = history_response.json()
        assert any(r["id"] == recording_id for r in history_data["items"])

    @pytest.mark.asyncio
    async def test_admin_journey(self, async_client: AsyncClient):
        """Test admin user journey with administrative functions."""
        # Step 1: Create an admin user
        admin_data = {
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "Admin User",
            "password": "adminpassword123",
            "confirm_password": "adminpassword123",
            "role": "admin"  # This would typically be set by another admin
        }
        
        register_response = await async_client.post("/api/auth/register", json=admin_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # Step 2: Login as admin
        login_data = {
            "email": admin_data["email"],
            "password": admin_data["password"]
        }
        
        login_response = await async_client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        tokens = login_response.json()
        admin_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Step 3: Access admin dashboard
        dashboard_response = await async_client.get("/api/admin/dashboard", headers=admin_headers)
        assert dashboard_response.status_code == status.HTTP_200_OK
        
        dashboard_data = dashboard_response.json()
        assert "users_count" in dashboard_data
        assert "quotes_count" in dashboard_data
        
        # Step 4: Get user list
        users_response = await async_client.get("/api/admin/users", headers=admin_headers)
        assert users_response.status_code == status.HTTP_200_OK
        
        users_data = users_response.json()
        assert "items" in users_data
        assert len(users_data["items"]) >= 1
        
        # Step 5: Get system analytics
        analytics_response = await async_client.get("/api/admin/analytics", headers=admin_headers)
        assert analytics_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_quote_discovery_journey(self, async_client: AsyncClient, auth_headers):
        """Test quote discovery and interaction journey."""
        # Step 1: Search for quotes
        search_response = await async_client.get(
            "/api/quotes/search", 
            params={"q": "success", "category": "motivation"}, 
            headers=auth_headers
        )
        assert search_response.status_code == status.HTTP_200_OK
        
        # Step 2: Browse quote categories
        categories_response = await async_client.get("/api/quotes/categories")
        assert categories_response.status_code == status.HTTP_200_OK
        
        categories = categories_response.json()
        assert len(categories) > 0
        
        # Step 3: Get quotes by category
        if categories:
            category_slug = categories[0]["slug"]
            category_quotes_response = await async_client.get(
                f"/api/quotes/category/{category_slug}", 
                headers=auth_headers
            )
            assert category_quotes_response.status_code == status.HTTP_200_OK
        
        # Step 4: Generate a new quote and interact with it
        quote_request = {
            "prompt": "Generate a quote about learning",
            "category": "education"
        }
        
        with patch('src.services.ai.orchestrator.AIOrchestrator.generate_quote') as mock_generate:
            mock_generate.return_value = {
                "text": "Learning never exhausts the mind.",
                "author": "Leonardo da Vinci",
                "quality_score": 9.1,
                "category": "education"
            }
            
            generate_response = await async_client.post(
                "/api/quotes/generate", 
                json=quote_request, 
                headers=auth_headers
            )
            
            assert generate_response.status_code == status.HTTP_201_CREATED
            quote_id = generate_response.json()["id"]
        
        # Step 5: Generate variations of the quote
        with patch('src.services.quote.engine.QuoteEngine.generate_variations') as mock_variations:
            mock_variations.return_value = [
                "The mind is never exhausted by learning.",
                "Learning continuously energizes the mind.",
                "A mind that learns never grows tired."
            ]
            
            variations_response = await async_client.post(
                f"/api/quotes/{quote_id}/variations", 
                json={"count": 3}, 
                headers=auth_headers
            )
            
            assert variations_response.status_code == status.HTTP_200_OK
            variations_data = variations_response.json()
            assert len(variations_data["variations"]) == 3
        
        # Step 6: Share the quote (mock external sharing)
        share_response = await async_client.post(
            f"/api/quotes/{quote_id}/share", 
            json={"platform": "twitter"}, 
            headers=auth_headers
        )
        assert share_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_analytics_journey(self, async_client: AsyncClient, auth_headers):
        """Test user analytics and insights journey."""
        # Step 1: Get user analytics dashboard
        analytics_response = await async_client.get("/api/analytics/dashboard", headers=auth_headers)
        assert analytics_response.status_code == status.HTTP_200_OK
        
        analytics_data = analytics_response.json()
        assert "quotes_generated" in analytics_data
        assert "total_views" in analytics_data
        
        # Step 2: Get detailed analytics
        detailed_response = await async_client.get(
            "/api/analytics/detailed", 
            params={"period": "30d"}, 
            headers=auth_headers
        )
        assert detailed_response.status_code == status.HTTP_200_OK
        
        # Step 3: Track a custom event
        event_data = {
            "event_type": "feature_used",
            "event_name": "quote_variations_generated",
            "properties": {
                "variations_count": 3,
                "quote_category": "motivation"
            }
        }
        
        track_response = await async_client.post(
            "/api/analytics/track", 
            json=event_data, 
            headers=auth_headers
        )
        assert track_response.status_code == status.HTTP_200_OK