"""
Unified Service Quote Generator for Window & Pressure Cleaning Pro

This service orchestrates multiple AI providers for intelligent service quote generation
with advanced features including job complexity assessment, pricing optimization,
A/B testing, quality validation, and smart fallback mechanisms.

Key Features:
- Multi-provider AI orchestration for service quote generation
- Advanced job assessment based on property type and cleaning requirements
- Service complexity analysis and pricing optimization
- A/B testing framework for different pricing strategies
- Quality validation and pricing accuracy checks
- Intelligent caching and fallback mechanisms for service quotes
- Comprehensive analytics and service metrics

Author: Window & Pressure Cleaning Pro Development Team
Version: 2.0.0
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import numpy as np
from textblob import TextBlob
try:
    import spacy
except ImportError:
    spacy = None
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None

from src.services.ai.ai_service import (
    AIService, AIRequest, AIResponse, AIProvider, ServiceCategory,
    get_ai_service
)
from src.services.quote.engine import QuoteEngine
from src.services.quote.service_quote import ServiceQuoteService
from src.core.exceptions import AIServiceError, RateLimitError, ServiceQuoteException
from src.core.config import get_settings
from src.models.service_quote import ServiceQuote


# Configure logging
logger = logging.getLogger(__name__)
settings = get_settings()

# Load spaCy model for advanced NLP
try:
    if spacy:
        nlp = spacy.load("en_core_web_sm")
    else:
        nlp = None
except (OSError, AttributeError):
    logger.warning("spaCy model 'en_core_web_sm' not found. Some features will be limited.")
    nlp = None


class ServiceType(Enum):
    """Types of cleaning services offered."""
    WINDOW_CLEANING = "window_cleaning"
    PRESSURE_WASHING = "pressure_washing"
    GUTTER_CLEANING = "gutter_cleaning"
    SOLAR_PANEL_CLEANING = "solar_panel_cleaning"
    ROOF_CLEANING = "roof_cleaning"
    DRIVEWAY_CLEANING = "driveway_cleaning"
    BUILDING_WASH = "building_wash"
    GRAFFITI_REMOVAL = "graffiti_removal"


class PropertyType(Enum):
    """Types of properties for service assessment."""
    RESIDENTIAL_HOUSE = "residential_house"
    RESIDENTIAL_APARTMENT = "residential_apartment"
    COMMERCIAL_OFFICE = "commercial_office"
    COMMERCIAL_RETAIL = "commercial_retail"
    INDUSTRIAL = "industrial"
    HOSPITALITY = "hospitality"
    HEALTHCARE = "healthcare"
    EDUCATIONAL = "educational"


class ComplexityLevel(Enum):
    """Job complexity levels for pricing."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    SPECIALIZED = "specialized"


class AccessDifficulty(Enum):
    """Access difficulty for service delivery."""
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    EXTREME = "extreme"


class PricingStrategy(Enum):
    """Pricing strategies for A/B testing."""
    COMPETITIVE = "competitive"
    PREMIUM = "premium"
    VALUE = "value"
    DYNAMIC = "dynamic"


class ABTestVariant(Enum):
    """A/B testing variants for different approaches."""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


@dataclass
class ServiceAssessment:
    """Assessment of service requirements and complexity."""
    primary_service: ServiceType
    complexity_level: ComplexityLevel
    access_difficulty: AccessDifficulty
    risk_factors: List[str]
    special_requirements: List[str]
    estimated_hours: float


@dataclass
class PropertyAnalysis:
    """Analysis of property characteristics for service planning."""
    property_type: PropertyType
    size_category: str  # "small", "medium", "large", "xl"
    access_score: float  # 0.0 = very difficult, 1.0 = very easy
    condition_score: float  # 0.0 = poor condition, 1.0 = excellent
    safety_considerations: List[str]


@dataclass
class CustomerProfile:
    """Customer profile for personalized service quotes."""
    customer_type: str  # "residential", "commercial", "industrial"
    price_sensitivity: str  # "budget", "standard", "premium"
    service_frequency: str  # "one-time", "regular", "seasonal"
    preferred_schedule: str  # "flexible", "specific", "urgent"
    communication_preference: str  # "email", "phone", "text"


@dataclass
class ServiceQuoteMetadata:
    """Comprehensive metadata for generated service quotes."""
    source_provider: AIProvider
    generation_time: datetime
    processing_duration: float
    quote_version: str
    accuracy_score: float
    service_assessment: ServiceAssessment
    property_analysis: PropertyAnalysis
    pricing_confidence: float
    pricing_strategy: PricingStrategy
    recommendations: List[str]
    risk_factors: List[str]
    cached: bool = False


@dataclass
class EnhancedServiceQuote:
    """Enhanced service quote response with comprehensive analysis."""
    service_type: ServiceType
    base_price: float
    total_price: float
    metadata: ServiceQuoteMetadata
    alternative_options: List[Dict[str, Any]] = field(default_factory=list)
    upsell_opportunities: List[str] = field(default_factory=list)
    terms_and_conditions: List[str] = field(default_factory=list)


class PromptTemplate:
    """Template for generating context-aware prompts."""
    
    def __init__(self, category: QuoteCategory, tone: ToneType, personality: PersonalityType):
        self.category = category
        self.tone = tone
        self.personality = personality
    
    def generate_prompt(self, base_prompt: str, context: Optional[str] = None) -> str:
        """Generate an enhanced prompt based on psychological profiling."""
        # Personality-based prompt modifications
        personality_modifiers = {
            PersonalityType.ACHIEVER: "Focus on success, goals, and achievement",
            PersonalityType.EXPLORER: "Emphasize discovery, adventure, and new experiences",
            PersonalityType.SOCIALIZER: "Highlight relationships, community, and connection",
            PersonalityType.THINKER: "Include wisdom, knowledge, and deep insights",
            PersonalityType.SUPPORTER: "Focus on helping others and making a difference",
            PersonalityType.CHALLENGER: "Emphasize overcoming obstacles and pushing limits"
        }
        
        # Tone-based instructions
        tone_instructions = {
            ToneType.INSPIRATIONAL: "Create an uplifting and inspiring message",
            ToneType.MOTIVATIONAL: "Generate a call-to-action that motivates behavior",
            ToneType.PROFESSIONAL: "Use professional language suitable for business",
            ToneType.CASUAL: "Keep it conversational and approachable",
            ToneType.FORMAL: "Use formal, respectful language",
            ToneType.HUMOROUS: "Add appropriate humor and lightness",
            ToneType.SERIOUS: "Maintain a serious, thoughtful tone",
            ToneType.OPTIMISTIC: "Focus on positive outcomes and hope",
            ToneType.REALISTIC: "Balance optimism with practical wisdom"
        }
        
        # Category-specific enhancements
        category_context = {
            QuoteCategory.MOTIVATIONAL: "that empowers and energizes the reader",
            QuoteCategory.INSPIRATIONAL: "that sparks hope and possibility",
            QuoteCategory.PROFESSIONAL: "that is suitable for workplace and business contexts",
            QuoteCategory.PERSONAL: "that resonates with personal growth and self-reflection"
        }
        
        # Build enhanced prompt
        enhanced_prompt = f"""
        Generate a {self.category.value} quote {category_context.get(self.category, '')}.
        
        Base concept: {base_prompt}
        {f'Context: {context}' if context else ''}
        
        Style guidelines:
        - {tone_instructions.get(self.tone, 'Maintain appropriate tone')}
        - {personality_modifiers.get(self.personality, 'Consider the target audience')}
        
        Requirements:
        - Create an original, memorable quote
        - Ensure it's practical and actionable
        - Make it emotionally resonant
        - Keep it concise but impactful
        - Avoid clichés and overused phrases
        
        Return only the quote text without additional explanation.
        """
        
        return enhanced_prompt.strip()


class EmotionAnalyzer:
    """Analyzes emotions in text using multiple approaches."""
    
    def __init__(self):
        # Emotion keywords for basic analysis
        self.emotion_keywords = {
            EmotionType.JOY: ["happy", "joy", "delight", "cheerful", "elated", "bliss", "content"],
            EmotionType.SADNESS: ["sad", "sorrow", "grief", "melancholy", "despair", "mourn"],
            EmotionType.ANGER: ["angry", "rage", "fury", "irritated", "indignant", "wrath"],
            EmotionType.FEAR: ["fear", "afraid", "terror", "anxiety", "worry", "dread"],
            EmotionType.SURPRISE: ["surprise", "amazed", "astonished", "shocked", "wonder"],
            EmotionType.TRUST: ["trust", "faith", "confidence", "belief", "reliance"],
            EmotionType.ANTICIPATION: ["hope", "expect", "anticipate", "eager", "optimism"]
        }
    
    def analyze_emotions(self, text: str) -> EmotionAnalysis:
        """Analyze emotions in the given text."""
        try:
            # Basic sentiment analysis using TextBlob
            blob = TextBlob(text)
            sentiment_polarity = blob.sentiment.polarity
            sentiment_subjectivity = blob.sentiment.subjectivity
        except Exception:
            sentiment_polarity = 0.0
            sentiment_subjectivity = 0.5
        
        # Calculate emotion scores based on keywords
        emotion_scores = {}
        text_lower = text.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower) / len(keywords)
            emotion_scores[emotion] = score
        
        # Adjust scores based on sentiment polarity
        if sentiment_polarity > 0:
            emotion_scores[EmotionType.JOY] += sentiment_polarity * 0.5
            emotion_scores[EmotionType.TRUST] += sentiment_polarity * 0.3
        elif sentiment_polarity < 0:
            emotion_scores[EmotionType.SADNESS] += abs(sentiment_polarity) * 0.4
            emotion_scores[EmotionType.ANGER] += abs(sentiment_polarity) * 0.3
        
        # Find primary emotion
        primary_emotion = max(emotion_scores, key=lambda k: emotion_scores[k])
        
        # Calculate emotional intensity and complexity
        emotional_intensity = abs(sentiment_polarity) + sentiment_subjectivity
        emotional_complexity = len([score for score in emotion_scores.values() if score > 0.1])
        
        return EmotionAnalysis(
            primary_emotion=primary_emotion,
            emotion_scores=emotion_scores,
            emotional_intensity=emotional_intensity,
            emotional_complexity=emotional_complexity
        )


class ToneAnalyzer:
    """Analyzes tone and style in text."""
    
    def __init__(self):
        # Tone indicators
        self.tone_indicators = {
            ToneType.INSPIRATIONAL: ["inspire", "dream", "achieve", "possibility", "potential"],
            ToneType.MOTIVATIONAL: ["action", "do", "start", "begin", "take", "move"],
            ToneType.PROFESSIONAL: ["strategy", "business", "success", "professional", "career"],
            ToneType.CASUAL: ["you", "we", "let's", "simple", "easy", "just"],
            ToneType.FORMAL: ["therefore", "furthermore", "consequently", "thus", "moreover"],
            ToneType.HUMOROUS: ["fun", "laugh", "smile", "enjoy", "playful", "light"],
            ToneType.SERIOUS: ["important", "critical", "essential", "must", "serious"],
            ToneType.OPTIMISTIC: ["will", "can", "positive", "bright", "hope", "better"],
            ToneType.REALISTIC: ["reality", "practical", "actually", "truth", "real"]
        }
    
    def analyze_tone(self, text: str) -> ToneAnalysis:
        """Analyze tone in the given text."""
        text_lower = text.lower()
        
        # Calculate tone scores
        tone_scores = {}
        for tone, indicators in self.tone_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower) / len(indicators)
            tone_scores[tone] = score
        
        # Find primary tone
        primary_tone = max(tone_scores, key=lambda k: tone_scores[k]) if tone_scores else ToneType.INSPIRATIONAL
        
        # Calculate formality score
        formal_words = ["therefore", "furthermore", "consequently", "moreover", "thus"]
        informal_words = ["you", "we", "let's", "just", "really", "pretty"]
        
        formal_count = sum(1 for word in formal_words if word in text_lower)
        informal_count = sum(1 for word in informal_words if word in text_lower)
        
        formality_score = (formal_count - informal_count + 1) / 2  # Normalize to 0-1
        
        # Calculate confidence level based on certainty words
        certainty_words = ["will", "always", "never", "definitely", "certainly", "absolutely"]
        uncertainty_words = ["might", "maybe", "perhaps", "possibly", "could", "may"]
        
        certainty_count = sum(1 for word in certainty_words if word in text_lower)
        uncertainty_count = sum(1 for word in uncertainty_words if word in text_lower)
        
        confidence_level = (certainty_count - uncertainty_count + 1) / 2  # Normalize to 0-1
        
        return ToneAnalysis(
            primary_tone=primary_tone,
            tone_scores=tone_scores,
            formality_score=formality_score,
            confidence_level=confidence_level
        )


class QualityValidator:
    """Validates and scores quote quality with improvement suggestions."""
    
    def __init__(self):
        self.min_length = 20
        self.max_length = 300
        self.ideal_length_range = (50, 150)
        
        # Common clichés to avoid
        self.cliches = [
            "think outside the box", "at the end of the day", "it is what it is",
            "everything happens for a reason", "when life gives you lemons",
            "follow your dreams", "believe in yourself", "you only live once"
        ]
    
    def validate_quality(self, text: str, category: QuoteCategory, 
                        emotion_analysis: EmotionAnalysis, tone_analysis: ToneAnalysis) -> Tuple[float, List[str]]:
        """Validate quote quality and provide improvement suggestions."""
        score = 1.0
        suggestions = []
        
        # Length validation
        length = len(text)
        if length < self.min_length:
            score -= 0.3
            suggestions.append("Quote is too short. Consider adding more substance.")
        elif length > self.max_length:
            score -= 0.2
            suggestions.append("Quote is too long. Consider making it more concise.")
        elif not (self.ideal_length_range[0] <= length <= self.ideal_length_range[1]):
            score -= 0.1
            suggestions.append("Consider adjusting length for optimal impact.")
        
        # Cliché detection
        text_lower = text.lower()
        cliche_count = sum(1 for cliche in self.cliches if cliche in text_lower)
        if cliche_count > 0:
            score -= 0.2 * cliche_count
            suggestions.append("Avoid overused phrases and clichés for originality.")
        
        # Emotional resonance
        if emotion_analysis.emotional_intensity < 0.3:
            score -= 0.15
            suggestions.append("Increase emotional impact for better resonance.")
        
        # Confidence and clarity
        if tone_analysis.confidence_level < 0.4:
            score -= 0.1
            suggestions.append("Use more confident language for stronger impact.")
        
        # Category alignment
        category_keywords = {
            QuoteCategory.MOTIVATIONAL: ["action", "achieve", "success", "goal"],
            QuoteCategory.INSPIRATIONAL: ["dream", "hope", "inspire", "possibility"],
            QuoteCategory.PROFESSIONAL: ["business", "career", "professional", "leadership"],
        }
        
        if category in category_keywords:
            keywords = category_keywords[category]
            keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
            if keyword_count == 0:
                score -= 0.1
                suggestions.append(f"Consider including themes related to {category.value}.")
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        # Add positive feedback for high-quality quotes
        if score > 0.8:
            suggestions.insert(0, "Excellent quote! High quality and impact.")
        elif score > 0.6:
            suggestions.insert(0, "Good quote with room for minor improvements.")
        
        return score, suggestions


class ABTestManager:
    """Manages A/B testing for different quote generation strategies."""
    
    def __init__(self):
        self.variant_weights = {
            ABTestVariant.CONTROL: 0.4,
            ABTestVariant.VARIANT_A: 0.3,
            ABTestVariant.VARIANT_B: 0.2,
            ABTestVariant.VARIANT_C: 0.1
        }
        self.results_cache = {}
    
    def select_variant(self, user_id: Optional[str] = None) -> ABTestVariant:
        """Select A/B test variant for the user."""
        # Use user_id for consistent variant assignment
        if user_id:
            # Hash user_id to get consistent variant
            hash_value = hash(user_id) % 100
            cumulative = 0
            for variant, weight in self.variant_weights.items():
                cumulative += weight * 100
                if hash_value < cumulative:
                    return variant
        
        # Random selection if no user_id
        return random.choices(
            list(self.variant_weights.keys()),
            weights=list(self.variant_weights.values())
        )[0]
    
    def get_variant_prompt_strategy(self, variant: ABTestVariant) -> Dict[str, Any]:
        """Get prompt strategy based on A/B test variant."""
        strategies = {
            ABTestVariant.CONTROL: {
                "temperature": 0.7,
                "approach": "standard",
                "emphasis": "balanced"
            },
            ABTestVariant.VARIANT_A: {
                "temperature": 0.8,
                "approach": "creative",
                "emphasis": "emotion"
            },
            ABTestVariant.VARIANT_B: {
                "temperature": 0.6,
                "approach": "practical",
                "emphasis": "action"
            },
            ABTestVariant.VARIANT_C: {
                "temperature": 0.9,
                "approach": "innovative",
                "emphasis": "metaphor"
            }
        }
        return strategies.get(variant, strategies[ABTestVariant.CONTROL])
    
    def record_result(self, variant: ABTestVariant, quality_score: float, user_feedback: Optional[float] = None):
        """Record A/B test result for analysis."""
        if variant not in self.results_cache:
            self.results_cache[variant] = {"scores": [], "feedback": []}
        
        self.results_cache[variant]["scores"].append(quality_score)
        if user_feedback is not None:
            self.results_cache[variant]["feedback"].append(user_feedback)
    
    def get_performance_metrics(self) -> Dict[ABTestVariant, Dict[str, float]]:
        """Get performance metrics for all variants."""
        metrics = {}
        for variant, data in self.results_cache.items():
            if data["scores"]:
                metrics[variant] = {
                    "avg_quality": np.mean(data["scores"]),
                    "count": len(data["scores"]),
                    "avg_feedback": np.mean(data["feedback"]) if data["feedback"] else 0.0
                }
        return metrics


class CacheManager:
    """Manages intelligent caching of quotes with fallback mechanisms."""
    
    def __init__(self):
        self.quote_cache = {}
        self.fallback_quotes = self._load_fallback_quotes()
        self.cache_ttl = 3600  # 1 hour
    
    def _load_fallback_quotes(self) -> Dict[QuoteCategory, List[str]]:
        """Load high-quality fallback quotes for each category."""
        return {
            QuoteCategory.MOTIVATIONAL: [
                "The only way to do great work is to love what you do.",
                "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "Your limitation—it's only your imagination.",
                "Great things never come from comfort zones."
            ],
            QuoteCategory.INSPIRATIONAL: [
                "The future belongs to those who believe in the beauty of their dreams.",
                "It is during our darkest moments that we must focus to see the light.",
                "Believe you can and you're halfway there.",
                "The only impossible journey is the one you never begin."
            ],
            QuoteCategory.PROFESSIONAL: [
                "Excellence is not a destination; it is a continuous journey that never ends.",
                "Leadership is not about being in charge. It is about taking care of those in your charge.",
                "Innovation distinguishes between a leader and a follower.",
                "The way to get started is to quit talking and begin doing."
            ]
        }
    
    def get_cache_key(self, request_params: Dict[str, Any]) -> str:
        """Generate cache key for request parameters."""
        key_components = [
            request_params.get("prompt", ""),
            request_params.get("category", ""),
            request_params.get("tone", ""),
            request_params.get("personality", "")
        ]
        return str(hash(str(key_components)))
    
    def get_cached_quote(self, cache_key: str) -> Optional[EnhancedQuoteResponse]:
        """Get cached quote if available and not expired."""
        if cache_key in self.quote_cache:
            cached_data = self.quote_cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < timedelta(seconds=self.cache_ttl):
                response = cached_data["response"]
                response.metadata.cached = True
                return response
        return None
    
    def cache_quote(self, cache_key: str, response: EnhancedQuoteResponse):
        """Cache quote response."""
        self.quote_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }
    
    def get_fallback_quote(self, category: QuoteCategory) -> str:
        """Get a fallback quote when all providers fail."""
        if category in self.fallback_quotes:
            return random.choice(self.fallback_quotes[category])
        
        # Generic fallback
        return "Every moment is a fresh beginning."


class UnifiedQuoteGenerator:
    """
    Unified quote generator that orchestrates multiple AI providers with
    advanced psychological profiling, emotion detection, and quality validation.
    """
    
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        emotion_analyzer: Optional[EmotionAnalyzer] = None,
        tone_analyzer: Optional[ToneAnalyzer] = None,
        quality_validator: Optional[QualityValidator] = None,
        ab_test_manager: Optional[ABTestManager] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """Initialize the unified quote generator with dependency injection."""
        self.ai_service = ai_service or AIService()
        self.emotion_analyzer = emotion_analyzer or EmotionAnalyzer()
        self.tone_analyzer = tone_analyzer or ToneAnalyzer()
        self.quality_validator = quality_validator or QualityValidator()
        self.ab_test_manager = ab_test_manager or ABTestManager()
        self.cache_manager = cache_manager or CacheManager()
        
        # Legacy services for backward compatibility
        self.quote_engine = QuoteEngine()
        self.service_quote_service = ServiceQuoteService()
        
        self.settings = get_settings()
        logger.info("Unified Quote Generator initialized with all components")
    
    def _infer_personality_type(self, context: str = None, user_history: List[str] = None) -> PersonalityType:
        """Infer personality type from context and user history."""
        if not context and not user_history:
            return PersonalityType.ACHIEVER  # Default
        
        text_to_analyze = f"{context or ''} {' '.join(user_history or [])}"
        text_lower = text_to_analyze.lower()
        
        # Keyword-based personality inference
        personality_indicators = {
            PersonalityType.ACHIEVER: ["success", "goal", "achieve", "win", "accomplish"],
            PersonalityType.EXPLORER: ["adventure", "discover", "explore", "new", "journey"],
            PersonalityType.SOCIALIZER: ["people", "team", "together", "community", "relationship"],
            PersonalityType.THINKER: ["understand", "analyze", "think", "wisdom", "knowledge"],
            PersonalityType.SUPPORTER: ["help", "support", "care", "serve", "assist"],
            PersonalityType.CHALLENGER: ["challenge", "overcome", "push", "break", "exceed"]
        }
        
        scores = {}
        for personality, keywords in personality_indicators.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[personality] = score
        
        return max(scores, key=lambda k: scores[k]) if scores else PersonalityType.ACHIEVER
    
    def _create_psychological_profile(
        self,
        personality_type: PersonalityType,
        tone: ToneType,
        context: str = None
    ) -> PsychologicalProfile:
        """Create a psychological profile for personalized quote generation."""
        # Define motivation triggers by personality type
        motivation_triggers = {
            PersonalityType.ACHIEVER: ["success", "goals", "achievement", "excellence", "victory"],
            PersonalityType.EXPLORER: ["adventure", "discovery", "growth", "experience", "journey"],
            PersonalityType.SOCIALIZER: ["connection", "impact", "community", "relationships", "helping"],
            PersonalityType.THINKER: ["wisdom", "understanding", "insight", "knowledge", "truth"],
            PersonalityType.SUPPORTER: ["service", "contribution", "making a difference", "caring", "support"],
            PersonalityType.CHALLENGER: ["obstacles", "limits", "breakthrough", "transformation", "courage"]
        }
        
        # Define emotional preferences
        emotional_preferences = {
            PersonalityType.ACHIEVER: [EmotionType.JOY, EmotionType.ANTICIPATION],
            PersonalityType.EXPLORER: [EmotionType.SURPRISE, EmotionType.ANTICIPATION],
            PersonalityType.SOCIALIZER: [EmotionType.JOY, EmotionType.TRUST],
            PersonalityType.THINKER: [EmotionType.TRUST, EmotionType.ANTICIPATION],
            PersonalityType.SUPPORTER: [EmotionType.TRUST, EmotionType.JOY],
            PersonalityType.CHALLENGER: [EmotionType.ANGER, EmotionType.ANTICIPATION]  # Controlled anger for motivation
        }
        
        # Complexity and length preferences
        complexity_prefs = {
            PersonalityType.ACHIEVER: 0.6,
            PersonalityType.EXPLORER: 0.7,
            PersonalityType.SOCIALIZER: 0.5,
            PersonalityType.THINKER: 0.8,
            PersonalityType.SUPPORTER: 0.5,
            PersonalityType.CHALLENGER: 0.7
        }
        
        length_prefs = {
            PersonalityType.ACHIEVER: "medium",
            PersonalityType.EXPLORER: "long",
            PersonalityType.SOCIALIZER: "short",
            PersonalityType.THINKER: "long",
            PersonalityType.SUPPORTER: "medium",
            PersonalityType.CHALLENGER: "short"
        }
        
        return PsychologicalProfile(
            personality_type=personality_type,
            motivation_triggers=motivation_triggers.get(personality_type, []),
            preferred_tone=tone,
            emotional_preferences=emotional_preferences.get(personality_type, []),
            complexity_preference=complexity_prefs.get(personality_type, 0.6),
            length_preference=length_prefs.get(personality_type, "medium")
        )
    
    async def _generate_with_provider_strategy(
        self,
        prompt: str,
        category: QuoteCategory,
        variant: ABTestVariant,
        context: str = None
    ) -> Optional[AIResponse]:
        """Generate quote using provider-specific strategy based on A/B variant."""
        try:
            strategy = self.ab_test_manager.get_variant_prompt_strategy(variant)
            
            # Create AI request with variant-specific parameters
            request = AIRequest(
                prompt=prompt,
                context=context,
                category=category,
                temperature=strategy["temperature"],
                max_tokens=200 if strategy["approach"] == "practical" else 250
            )
            
            # Try to generate with primary strategy
            response = await self.ai_service.generate_quote(request)
            return response
            
        except Exception as e:
            logger.warning(f"Provider strategy failed for variant {variant}: {e}")
            return None
    
    async def generate_enhanced_quote(
        self,
        prompt: str,
        category: QuoteCategory = QuoteCategory.MOTIVATIONAL,
        tone: ToneType = ToneType.INSPIRATIONAL,
        context: str = None,
        user_id: str = None,
        user_history: List[str] = None,
        generate_alternatives: bool = True
    ) -> EnhancedQuoteResponse:
        """
        Generate an enhanced quote with comprehensive analysis and metadata.
        
        Args:
            prompt: Base prompt for quote generation
            category: Quote category
            tone: Desired tone
            context: Additional context
            user_id: User identifier for personalization
            user_history: User's quote history for personalization
            generate_alternatives: Whether to generate alternative quotes
            
        Returns:
            EnhancedQuoteResponse with comprehensive analysis
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_params = {
                "prompt": prompt,
                "category": category.value,
                "tone": tone.value,
                "context": context
            }
            cache_key = self.cache_manager.get_cache_key(cache_params)
            cached_response = self.cache_manager.get_cached_quote(cache_key)
            
            if cached_response:
                logger.info("Returning cached quote response")
                return cached_response
            
            # Infer personality type
            personality_type = self._infer_personality_type(context, user_history)
            
            # Create psychological profile
            psychological_profile = self._create_psychological_profile(personality_type, tone, context)
            
            # Select A/B test variant
            ab_variant = self.ab_test_manager.select_variant(user_id)
            
            # Create enhanced prompt template
            prompt_template = PromptTemplate(category, tone, personality_type)
            enhanced_prompt = prompt_template.generate_prompt(prompt, context)
            
            # Generate primary quote
            primary_response = await self._generate_with_provider_strategy(
                enhanced_prompt, category, ab_variant, context
            )
            
            if not primary_response:
                # Fallback to cached quote
                fallback_text = self.cache_manager.get_fallback_quote(category)
                primary_response = AIResponse(
                    text=fallback_text,
                    provider=AIProvider.OPENAI,  # Placeholder
                    model="fallback",
                    tokens_used=0,
                    cost=0.0,
                    quality_score=0.7,
                    response_time=0.1,
                    timestamp=datetime.now(),
                    request_id="fallback",
                    cached=True
                )
            
            # Analyze emotions and tone
            emotion_analysis = self.emotion_analyzer.analyze_emotions(primary_response.text)
            tone_analysis = self.tone_analyzer.analyze_tone(primary_response.text)
            
            # Validate quality and get improvement suggestions
            quality_score, improvement_suggestions = self.quality_validator.validate_quality(
                primary_response.text, category, emotion_analysis, tone_analysis
            )
            
            # Calculate psychological match
            psychological_match = self._calculate_psychological_match(
                primary_response.text, psychological_profile
            )
            
            # Generate alternatives if requested
            alternatives = []
            if generate_alternatives and not primary_response.cached:
                try:
                    alternative_variants = [v for v in ABTestVariant if v != ab_variant][:2]
                    for variant in alternative_variants:
                        alt_response = await self._generate_with_provider_strategy(
                            enhanced_prompt, category, variant, context
                        )
                        if alt_response:
                            alternatives.append(alt_response.text)
                except Exception as e:
                    logger.warning(f"Failed to generate alternatives: {e}")
            
            # Extract related themes and usage recommendations
            related_themes = self._extract_themes(primary_response.text)
            usage_recommendations = self._generate_usage_recommendations(
                category, tone, psychological_profile
            )
            
            # Create metadata
            metadata = QuoteMetadata(
                source_provider=primary_response.provider,
                generation_time=datetime.now(),
                processing_duration=time.time() - start_time,
                prompt_version="v2.0",
                quality_score=quality_score,
                emotion_analysis=emotion_analysis,
                tone_analysis=tone_analysis,
                psychological_match=psychological_match,
                ab_test_variant=ab_variant,
                improvement_suggestions=improvement_suggestions,
                confidence_score=min(quality_score + psychological_match, 1.0),
                cached=primary_response.cached
            )
            
            # Create enhanced response
            enhanced_response = EnhancedQuoteResponse(
                text=primary_response.text,
                category=category,
                metadata=metadata,
                alternatives=alternatives,
                related_themes=related_themes,
                usage_recommendations=usage_recommendations
            )
            
            # Cache the response
            if not primary_response.cached:
                self.cache_manager.cache_quote(cache_key, enhanced_response)
            
            # Record A/B test result
            self.ab_test_manager.record_result(ab_variant, quality_score)
            
            logger.info(f"Generated enhanced quote with quality score: {quality_score:.2f}")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced quote: {e}")
            
            # Emergency fallback
            fallback_text = self.cache_manager.get_fallback_quote(category)
            
            # Create minimal metadata
            metadata = QuoteMetadata(
                source_provider=AIProvider.OPENAI,
                generation_time=datetime.now(),
                processing_duration=time.time() - start_time,
                prompt_version="fallback",
                quality_score=0.5,
                emotion_analysis=EmotionAnalysis(
                    primary_emotion=EmotionType.JOY,
                    emotion_scores={},
                    emotional_intensity=0.5,
                    emotional_complexity=1.0
                ),
                tone_analysis=ToneAnalysis(
                    primary_tone=tone,
                    tone_scores={},
                    formality_score=0.5,
                    confidence_level=0.5
                ),
                psychological_match=0.5,
                ab_test_variant=ABTestVariant.CONTROL,
                improvement_suggestions=["This is a fallback quote. Try again for a personalized result."],
                confidence_score=0.3,
                cached=True
            )
            
            return EnhancedQuoteResponse(
                text=fallback_text,
                category=category,
                metadata=metadata
            )
    
    def _calculate_psychological_match(self, text: str, profile: PsychologicalProfile) -> float:
        """Calculate how well the quote matches the psychological profile."""
        text_lower = text.lower()
        match_score = 0.0
        
        # Check motivation triggers
        trigger_matches = sum(1 for trigger in profile.motivation_triggers 
                            if trigger.lower() in text_lower)
        if profile.motivation_triggers:
            match_score += (trigger_matches / len(profile.motivation_triggers)) * 0.4
        
        # Check tone alignment
        tone_indicators = {
            ToneType.INSPIRATIONAL: ["inspire", "dream", "achieve", "possibility"],
            ToneType.MOTIVATIONAL: ["action", "do", "start", "move"],
            # Add more as needed
        }
        
        if profile.preferred_tone in tone_indicators:
            indicators = tone_indicators[profile.preferred_tone]
            indicator_matches = sum(1 for indicator in indicators if indicator in text_lower)
            match_score += (indicator_matches / len(indicators)) * 0.3
        
        # Check complexity preference
        text_complexity = self._calculate_text_complexity(text)
        complexity_diff = abs(text_complexity - profile.complexity_preference)
        match_score += (1.0 - complexity_diff) * 0.3
        
        return min(match_score, 1.0)
    
    def _calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity score (0.0 = simple, 1.0 = complex)."""
        # Word length
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Sentence complexity
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Syllable complexity (simplified)
        syllable_count = sum(max(1, len([c for c in word.lower() if c in 'aeiou'])) 
                           for word in words)
        avg_syllables = syllable_count / len(words) if words else 1
        
        # Normalize and combine
        word_complexity = min(avg_word_length / 8.0, 1.0)  # 8 chars = complex
        sentence_complexity = min(avg_sentence_length / 20.0, 1.0)  # 20 words = complex
        syllable_complexity = min(avg_syllables / 3.0, 1.0)  # 3 syllables = complex
        
        return (word_complexity + sentence_complexity + syllable_complexity) / 3.0
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from the quote."""
        themes = []
        
        # Common theme keywords
        theme_keywords = {
            "success": ["success", "achieve", "accomplish", "victory", "win"],
            "growth": ["grow", "develop", "improve", "progress", "evolve"],
            "courage": ["courage", "brave", "bold", "fearless", "strength"],
            "wisdom": ["wise", "knowledge", "understand", "learn", "insight"],
            "perseverance": ["persist", "continue", "endure", "overcome", "push"],
            "leadership": ["lead", "guide", "inspire", "influence", "direct"],
            "innovation": ["create", "innovate", "new", "different", "unique"],
            "teamwork": ["together", "team", "collaboration", "unity", "collective"]
        }
        
        text_lower = text.lower()
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        return themes[:5]  # Limit to top 5 themes
    
    def _generate_usage_recommendations(
        self, 
        category: QuoteCategory,
        tone: ToneType,
        profile: PsychologicalProfile
    ) -> List[str]:
        """Generate usage recommendations for the quote."""
        recommendations = []
        
        # Category-based recommendations
        category_usage = {
            QuoteCategory.MOTIVATIONAL: [
                "Use in morning motivation emails",
                "Post on social media for engagement",
                "Include in team meeting presentations"
            ],
            QuoteCategory.PROFESSIONAL: [
                "Include in business presentations",
                "Use in professional networking posts",
                "Add to email signatures"
            ],
            QuoteCategory.INSPIRATIONAL: [
                "Share during difficult times",
                "Use in personal development content",
                "Post on inspirational social feeds"
            ]
        }
        
        if category in category_usage:
            recommendations.extend(category_usage[category])
        
        # Tone-based recommendations
        if tone == ToneType.CASUAL:
            recommendations.append("Great for informal team communications")
        elif tone == ToneType.FORMAL:
            recommendations.append("Suitable for executive communications")
        
        # Personality-based recommendations
        personality_usage = {
            PersonalityType.ACHIEVER: "Perfect for goal-oriented individuals",
            PersonalityType.EXPLORER: "Great for adventure and travel content",
            PersonalityType.SOCIALIZER: "Ideal for community and team building"
        }
        
        if profile.personality_type in personality_usage:
            recommendations.append(personality_usage[profile.personality_type])
        
        return recommendations[:4]  # Limit to top 4 recommendations
    
    # Legacy methods for backward compatibility
    async def generate_inspirational_quote(
        self,
        prompt: str,
        style: Optional[str] = None,
        category: Optional[str] = None,
        length: str = "medium",
        model_preference: str = "auto"
    ) -> Dict[str, Any]:
        """Legacy method for inspirational quote generation."""
        try:
            # Map to new system
            quote_category = QuoteCategory.INSPIRATIONAL
            if category:
                try:
                    quote_category = QuoteCategory(category.lower())
                except ValueError:
                    quote_category = QuoteCategory.INSPIRATIONAL
            
            tone = ToneType.INSPIRATIONAL
            if style:
                try:
                    tone = ToneType(style.lower())
                except ValueError:
                    tone = ToneType.INSPIRATIONAL
            
            # Generate enhanced quote
            enhanced_response = await self.generate_enhanced_quote(
                prompt=prompt,
                category=quote_category,
                tone=tone
            )
            
            return {
                "content": enhanced_response.text,
                "author": "AI Generated",
                "category": category or "inspirational",
                "style": style or "inspirational",
                "confidence": enhanced_response.metadata.confidence_score,
                "model_used": enhanced_response.metadata.source_provider.value,
                "generation_time": enhanced_response.metadata.processing_duration,
                "metadata": {
                    "prompt": prompt,
                    "length": length,
                    "generated_at": enhanced_response.metadata.generation_time.isoformat(),
                    "service_used": "UnifiedQuoteGenerator"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate inspirational quote: {str(e)}")
            raise QuoteGenerationException(f"Quote generation failed: {str(e)}")
    
    async def generate_service_quote_from_voice(
        self,
        transcription: str,
        audio_metadata: Dict[str, Any],
        fallback_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Legacy method for service quote generation from voice."""
        try:
            # This would need to be implemented with actual service quote logic
            # For now, return a basic structure
            return {
                "service_quote": {"total_price": 0.0, "error": "Service quote calculation not implemented"},
                "extraction_confidence": 0.0,
                "extracted_data": {},
                "transcription": transcription,
                "ai_analysis": {},
                "recommendations": [],
                "metadata": {
                    "voice_processed": True,
                    "audio_duration": audio_metadata.get("duration", 0),
                    "audio_quality": audio_metadata.get("quality", "unknown"),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate service quote from voice: {str(e)}")
            raise QuoteGenerationException(f"Voice quote generation failed: {str(e)}")
    
    async def batch_generate_quotes(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[EnhancedQuoteResponse]:
        """Generate multiple quotes concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(request_params: Dict[str, Any]) -> EnhancedQuoteResponse:
            async with semaphore:
                return await self.generate_enhanced_quote(**request_params)
        
        tasks = [generate_single(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch request {i} failed: {response}")
            else:
                valid_responses.append(response)
        
        return valid_responses
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for the quote generation service."""
        try:
            # A/B test performance
            ab_metrics = self.ab_test_manager.get_performance_metrics()
            
            # AI service metrics
            ai_metrics = await self.ai_service.get_metrics()
            
            # Cache statistics
            cache_stats = {
                "total_cached": len(self.cache_manager.quote_cache),
                "cache_hit_rate": 0.0  # Would need to track this
            }
            
            return {
                "ab_test_performance": ab_metrics,
                "ai_service_metrics": ai_metrics,
                "cache_statistics": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e)}


# Convenience functions
async def generate_personalized_quote(
    prompt: str,
    category: QuoteCategory = QuoteCategory.MOTIVATIONAL,
    tone: ToneType = ToneType.INSPIRATIONAL,
    personality: PersonalityType = PersonalityType.ACHIEVER,
    user_id: str = None
) -> EnhancedQuoteResponse:
    """Generate a personalized quote with smart defaults."""
    generator = UnifiedQuoteGenerator()
    return await generator.generate_enhanced_quote(
        prompt=prompt,
        category=category,
        tone=tone,
        user_id=user_id
    )


async def generate_business_quote(
    topic: str,
    context: str = None,
    user_id: str = None
) -> EnhancedQuoteResponse:
    """Generate a business-focused quote."""
    generator = UnifiedQuoteGenerator()
    return await generator.generate_enhanced_quote(
        prompt=topic,
        category=QuoteCategory.PROFESSIONAL,
        tone=ToneType.PROFESSIONAL,
        context=f"Business context: {context}" if context else None,
        user_id=user_id
    )


async def generate_motivational_collection(
    themes: List[str],
    count_per_theme: int = 3
) -> Dict[str, List[EnhancedQuoteResponse]]:
    """Generate a collection of motivational quotes for different themes."""
    generator = UnifiedQuoteGenerator()
    results = {}
    
    for theme in themes:
        requests = [
            {
                "prompt": f"motivation about {theme}",
                "category": QuoteCategory.MOTIVATIONAL,
                "tone": ToneType.MOTIVATIONAL,
                "generate_alternatives": False
            }
            for _ in range(count_per_theme)
        ]
        
        theme_quotes = await generator.batch_generate_quotes(requests)
        results[theme] = theme_quotes
    
    return results


# Singleton instance
_unified_generator = None

def get_unified_generator() -> UnifiedQuoteGenerator:
    """Get singleton instance of UnifiedQuoteGenerator."""
    global _unified_generator
    if _unified_generator is None:
        _unified_generator = UnifiedQuoteGenerator()
    return _unified_generator


# Create singleton instance for backward compatibility
quote_generator = UnifiedQuoteGenerator()
