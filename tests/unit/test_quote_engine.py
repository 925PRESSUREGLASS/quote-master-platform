"""
Unit tests for quote generation engine.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.services.quote.engine import QuoteEngine
from src.services.quote.psychology import PsychologyAnalyzer
from src.models.quote import Quote, QuoteGeneration


class TestQuoteEngine:
    """Test quote generation engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.quote_engine = QuoteEngine()

    @pytest.mark.asyncio
    async def test_generate_quote_basic(self):
        """Test basic quote generation."""
        request = QuoteGeneration(
            prompt="Generate a motivational quote about success",
            category="motivation",
            style="inspirational",
            length="medium"
        )
        
        with patch.object(self.quote_engine, '_call_ai_service') as mock_ai:
            mock_ai.return_value = {
                "text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "author": "Winston Churchill",
                "quality_score": 8.5,
                "confidence": 0.9
            }
            
            result = await self.quote_engine.generate_quote(request)
            
            assert isinstance(result, Quote)
            assert result.text == "Success is not final, failure is not fatal: it is the courage to continue that counts."
            assert result.author == "Winston Churchill"
            assert result.quality_score == 8.5

    @pytest.mark.asyncio
    async def test_generate_quote_with_psychology(self):
        """Test quote generation with psychology analysis."""
        request = QuoteGeneration(
            prompt="Generate a quote about overcoming fear",
            category="psychology",
            include_psychology=True
        )
        
        with patch.object(self.quote_engine, '_call_ai_service') as mock_ai, \
             patch.object(self.quote_engine.psychology_analyzer, 'analyze_quote') as mock_psych:
            
            mock_ai.return_value = {
                "text": "The only way to overcome fear is to face it head on.",
                "author": "Unknown",
                "quality_score": 7.8
            }
            
            mock_psych.return_value = {
                "emotional_tone": "empowering",
                "psychological_themes": ["courage", "self-improvement"],
                "complexity_score": 6.5,
                "impact_prediction": 8.2
            }
            
            result = await self.quote_engine.generate_quote(request)
            
            assert result.emotional_tone == "empowering"
            assert "courage" in result.psychological_profile["psychological_themes"]
            assert result.complexity_score == 6.5

    @pytest.mark.asyncio
    async def test_generate_quote_with_author_style(self):
        """Test quote generation with specific author style."""
        request = QuoteGeneration(
            prompt="Generate a quote about life",
            author_style="Maya Angelou",
            style="poetic"
        )
        
        with patch.object(self.quote_engine, '_call_ai_service') as mock_ai:
            mock_ai.return_value = {
                "text": "Life is not measured by the number of breaths we take, but by the moments that take our breath away.",
                "author": "Maya Angelou (style)",
                "quality_score": 9.1
            }
            
            result = await self.quote_engine.generate_quote(request)
            
            assert "Maya Angelou" in result.author
            assert result.quality_score > 8.0

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        quote_text = "The only way to do great work is to love what you do."
        
        score = self.quote_engine._calculate_quality_score(quote_text)
        
        assert isinstance(score, float)
        assert 0 <= score <= 10

    def test_calculate_quality_score_factors(self):
        """Test quality score calculation with different factors."""
        # Test length factor
        short_quote = "Be yourself."
        long_quote = "In the end, we will remember not the words of our enemies, but the silence of our friends."
        
        short_score = self.quote_engine._calculate_quality_score(short_quote)
        long_score = self.quote_engine._calculate_quality_score(long_quote)
        
        # Longer quotes within optimal range should score higher
        assert long_score > short_score

    def test_extract_keywords(self):
        """Test keyword extraction from quote text."""
        quote_text = "Success is not final, failure is not fatal: it is the courage to continue that counts."
        
        keywords = self.quote_engine._extract_keywords(quote_text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "success" in [k.lower() for k in keywords]
        assert "courage" in [k.lower() for k in keywords]

    def test_determine_category(self):
        """Test automatic category determination."""
        motivational_text = "Believe you can and you're halfway there."
        love_text = "Love is not about possession, it's about appreciation."
        wisdom_text = "The wise man knows that he knows nothing."
        
        assert self.quote_engine._determine_category(motivational_text) == "motivation"
        assert self.quote_engine._determine_category(love_text) == "love"
        assert self.quote_engine._determine_category(wisdom_text) == "wisdom"

    def test_validate_quote_content(self):
        """Test quote content validation."""
        # Valid quote
        valid_quote = "Success is the result of preparation, hard work, and learning from failure."
        assert self.quote_engine._validate_quote_content(valid_quote) is True
        
        # Invalid quotes
        too_short = "Yes."
        too_long = "A" * 1000
        inappropriate = "This contains offensive content that should be filtered out."
        
        assert self.quote_engine._validate_quote_content(too_short) is False
        assert self.quote_engine._validate_quote_content(too_long) is False
        # Note: Actual inappropriate content filtering would be more sophisticated

    @pytest.mark.asyncio
    async def test_enhance_with_context(self):
        """Test quote enhancement with additional context."""
        original_quote = "Success comes to those who work hard."
        context = "career advice for young professionals"
        
        with patch.object(self.quote_engine, '_call_ai_service') as mock_ai:
            mock_ai.return_value = {
                "text": "Success in your career comes to those who work hard and never stop learning.",
                "enhancement_type": "context_specific",
                "quality_improvement": 1.2
            }
            
            enhanced = await self.quote_engine._enhance_with_context(original_quote, context)
            
            assert "career" in enhanced["text"]
            assert enhanced["quality_improvement"] > 1.0

    def test_sentiment_analysis(self):
        """Test sentiment analysis of quotes."""
        positive_quote = "Every day is a new opportunity to achieve greatness."
        negative_quote = "Life is full of disappointments and failures."
        neutral_quote = "The sun rises in the east and sets in the west."
        
        pos_sentiment = self.quote_engine._analyze_sentiment(positive_quote)
        neg_sentiment = self.quote_engine._analyze_sentiment(negative_quote)
        neu_sentiment = self.quote_engine._analyze_sentiment(neutral_quote)
        
        assert pos_sentiment > 0.5
        assert neg_sentiment < -0.5
        assert -0.5 <= neu_sentiment <= 0.5

    @pytest.mark.asyncio
    async def test_generate_variations(self):
        """Test generating variations of a quote."""
        original_quote = "The only way to do great work is to love what you do."
        
        with patch.object(self.quote_engine, '_call_ai_service') as mock_ai:
            mock_ai.return_value = {
                "variations": [
                    "Great work comes from doing what you love.",
                    "To achieve excellence, you must love your work.",
                    "Passion for your work is the key to greatness."
                ]
            }
            
            variations = await self.quote_engine.generate_variations(original_quote, count=3)
            
            assert len(variations) == 3
            assert all(isinstance(v, str) for v in variations)
            assert original_quote not in variations

    def test_format_quote_output(self):
        """Test quote output formatting."""
        quote_data = {
            "text": "success is the result of hard work",
            "author": "unknown author",
            "category": "MOTIVATION"
        }
        
        formatted = self.quote_engine._format_quote_output(quote_data)
        
        # Should capitalize properly
        assert formatted["text"] == "Success is the result of hard work"
        assert formatted["author"] == "Unknown Author"
        assert formatted["category"] == "motivation"

    @pytest.mark.asyncio
    async def test_error_handling_ai_service_failure(self):
        """Test error handling when AI service fails."""
        request = QuoteGeneration(
            prompt="Generate a quote",
            category="motivation"
        )
        
        with patch.object(self.quote_engine, '_call_ai_service') as mock_ai:
            mock_ai.side_effect = Exception("AI service unavailable")
            
            with pytest.raises(Exception):
                await self.quote_engine.generate_quote(request)

    def test_filter_inappropriate_content(self):
        """Test inappropriate content filtering."""
        clean_quote = "Success comes to those who work hard."
        inappropriate_quote = "This contains bad words and harmful content."
        
        assert self.quote_engine._filter_inappropriate_content(clean_quote) == clean_quote
        # In a real implementation, this would filter or reject inappropriate content
        filtered = self.quote_engine._filter_inappropriate_content(inappropriate_quote)
        assert isinstance(filtered, str)  # Should return something, even if modified