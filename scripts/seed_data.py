#!/usr/bin/env python3
"""
Seed database with sample data for Quote Master Pro.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from models.user import User
from models.quote import Quote, QuoteCategory
from models.voice import VoiceRecording
from services.auth import AuthService


async def create_sample_users(session: AsyncSession) -> list[User]:
    """Create sample users."""
    auth_service = AuthService()
    
    users_data = [
        {
            "email": "admin@quotemaster.pro",
            "username": "admin",
            "full_name": "Admin User",
            "password": "admin123",
            "role": "admin",
            "is_verified": True,
        },
        {
            "email": "john.doe@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "password": "user123",
            "role": "user",
            "is_verified": True,
        },
        {
            "email": "jane.smith@example.com",
            "username": "janesmith",
            "full_name": "Jane Smith",
            "password": "user123",
            "role": "premium",
            "is_verified": True,
            "bio": "Motivational speaker and life coach",
        },
        {
            "email": "mike.wilson@example.com",
            "username": "mikewilson",
            "full_name": "Mike Wilson",
            "password": "user123",
            "role": "user",
            "is_verified": False,
        }
    ]
    
    users = []
    for user_data in users_data:
        # Check if user already exists
        existing_user = await session.get(User, {"email": user_data["email"]})
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping...")
            users.append(existing_user)
            continue
        
        password = user_data.pop("password")
        user = User(
            **user_data,
            password_hash=auth_service.hash_password(password)
        )
        
        session.add(user)
        users.append(user)
        print(f"Created user: {user.email}")
    
    await session.commit()
    return users


async def create_sample_categories(session: AsyncSession) -> list[QuoteCategory]:
    """Create sample quote categories."""
    categories_data = [
        {
            "name": "Motivation",
            "slug": "motivation",
            "description": "Inspirational quotes to motivate and energize",
            "color": "#3b82f6",
            "icon": "💪",
            "sort_order": 1,
        },
        {
            "name": "Success",
            "slug": "success",
            "description": "Quotes about achieving success and goals",
            "color": "#10b981",
            "icon": "🎯",
            "sort_order": 2,
        },
        {
            "name": "Life",
            "slug": "life",
            "description": "Wisdom about life and living",
            "color": "#f59e0b",
            "icon": "🌟",
            "sort_order": 3,
        },
        {
            "name": "Love",
            "slug": "love",
            "description": "Quotes about love and relationships",
            "color": "#ef4444",
            "icon": "❤️",
            "sort_order": 4,
        },
        {
            "name": "Wisdom",
            "slug": "wisdom",
            "description": "Timeless wisdom and philosophical insights",
            "color": "#8b5cf6",
            "icon": "🧠",
            "sort_order": 5,
        },
        {
            "name": "Happiness",
            "slug": "happiness",
            "description": "Quotes about joy and contentment",
            "color": "#fbbf24",
            "icon": "😊",
            "sort_order": 6,
        },
        {
            "name": "Perseverance",
            "slug": "perseverance",
            "description": "Quotes about persistence and determination",
            "color": "#6366f1",
            "icon": "🏔️",
            "sort_order": 7,
        },
        {
            "name": "Leadership",
            "slug": "leadership",
            "description": "Insights on leadership and influence",
            "color": "#84cc16",
            "icon": "👑",
            "sort_order": 8,
        }
    ]
    
    categories = []
    for category_data in categories_data:
        # Check if category already exists
        existing_category = await session.execute(
            select(QuoteCategory).where(QuoteCategory.slug == category_data["slug"])
        )
        existing_category = existing_category.scalar_one_or_none()
        
        if existing_category:
            print(f"Category {category_data['name']} already exists, skipping...")
            categories.append(existing_category)
            continue
        
        category = QuoteCategory(**category_data)
        session.add(category)
        categories.append(category)
        print(f"Created category: {category.name}")
    
    await session.commit()
    return categories


async def create_sample_quotes(session: AsyncSession, users: list[User], categories: list[QuoteCategory]):
    """Create sample quotes."""
    quotes_data = [
        {
            "text": "The only way to do great work is to love what you do.",
            "author": "Steve Jobs",
            "category": "motivation",
            "quality_score": 9.2,
            "sentiment_score": 0.8,
        },
        {
            "text": "Life is what happens to you while you're busy making other plans.",
            "author": "John Lennon",
            "category": "life",
            "quality_score": 8.7,
            "sentiment_score": 0.3,
        },
        {
            "text": "The future belongs to those who believe in the beauty of their dreams.",
            "author": "Eleanor Roosevelt",
            "category": "motivation",
            "quality_score": 9.0,
            "sentiment_score": 0.9,
        },
        {
            "text": "It is during our darkest moments that we must focus to see the light.",
            "author": "Aristotle",
            "category": "wisdom",
            "quality_score": 8.9,
            "sentiment_score": 0.6,
        },
        {
            "text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "author": "Winston Churchill",
            "category": "success",
            "quality_score": 9.3,
            "sentiment_score": 0.7,
        },
        {
            "text": "The way to get started is to quit talking and begin doing.",
            "author": "Walt Disney",
            "category": "motivation",
            "quality_score": 8.5,
            "sentiment_score": 0.8,
        },
        {
            "text": "Don't let yesterday take up too much of today.",
            "author": "Will Rogers",
            "category": "life",
            "quality_score": 8.3,
            "sentiment_score": 0.6,
        },
        {
            "text": "You learn more from failure than from success. Don't let it stop you. Failure builds character.",
            "author": "Unknown",
            "category": "perseverance",
            "quality_score": 8.8,
            "sentiment_score": 0.7,
        },
        {
            "text": "If you are working on something that you really care about, you don't have to be pushed. The vision pulls you.",
            "author": "Steve Jobs",
            "category": "motivation",
            "quality_score": 9.1,
            "sentiment_score": 0.9,
        },
        {
            "text": "Happiness is not something ready made. It comes from your own actions.",
            "author": "Dalai Lama",
            "category": "happiness",
            "quality_score": 8.6,
            "sentiment_score": 0.8,
        }
    ]
    
    # Create category lookup
    category_lookup = {cat.slug: cat for cat in categories}
    
    for i, quote_data in enumerate(quotes_data):
        user = users[i % len(users)]  # Distribute quotes among users
        category_slug = quote_data.pop("category")
        category = category_lookup.get(category_slug)
        
        quote = Quote(
            user_id=user.id,
            category_id=category.id if category else None,
            source="imported",
            is_approved=True,
            is_public=True,
            **quote_data
        )
        
        session.add(quote)
        print(f"Created quote: {quote.text[:50]}...")
    
    await session.commit()


async def create_sample_voice_recordings(session: AsyncSession, users: list[User]):
    """Create sample voice recordings."""
    recordings_data = [
        {
            "filename": "motivation_speech.wav",
            "original_filename": "My Motivation Speech.wav",
            "file_path": "/uploads/voice/motivation_speech.wav",
            "file_size": 2048000,
            "file_format": "wav",
            "duration_seconds": 45.5,
            "transcription": "Success is not about being perfect, it's about being persistent. Every failure is a step closer to success.",
            "transcription_confidence": 0.92,
            "language_detected": "en",
            "status": "processed",
            "is_processed": True,
            "has_transcription": True,
        },
        {
            "filename": "life_advice.wav",
            "original_filename": "Life Advice Recording.wav",
            "file_path": "/uploads/voice/life_advice.wav",
            "file_size": 1536000,
            "file_format": "wav",
            "duration_seconds": 33.2,
            "transcription": "The most important thing in life is to be true to yourself and follow your passion.",
            "transcription_confidence": 0.88,
            "language_detected": "en",
            "status": "processed",
            "is_processed": True,
            "has_transcription": True,
        },
        {
            "filename": "daily_affirmation.wav",
            "original_filename": "Daily Affirmation.wav",
            "file_path": "/uploads/voice/daily_affirmation.wav",
            "file_size": 1024000,
            "file_format": "wav",
            "duration_seconds": 22.1,
            "transcription": "I am capable of achieving anything I set my mind to. Today is full of possibilities.",
            "transcription_confidence": 0.95,
            "language_detected": "en",
            "status": "processed",
            "is_processed": True,
            "has_transcription": True,
        }
    ]
    
    for i, recording_data in enumerate(recordings_data):
        user = users[i % len(users)]  # Distribute recordings among users
        
        recording = VoiceRecording(
            user_id=user.id,
            **recording_data
        )
        
        session.add(recording)
        print(f"Created voice recording: {recording.filename}")
    
    await session.commit()


async def main():
    """Main function to seed the database."""
    print("🌱 Starting database seeding...")
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Create sample data
            print("\n👥 Creating sample users...")
            users = await create_sample_users(session)
            
            print("\n📁 Creating sample categories...")
            categories = await create_sample_categories(session)
            
            print("\n💬 Creating sample quotes...")
            await create_sample_quotes(session, users, categories)
            
            print("\n🎤 Creating sample voice recordings...")
            await create_sample_voice_recordings(session, users)
            
            print("\n✅ Database seeding completed successfully!")
            print(f"Created {len(users)} users")
            print(f"Created {len(categories)} categories")
            print("Created 10 sample quotes")
            print("Created 3 sample voice recordings")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())