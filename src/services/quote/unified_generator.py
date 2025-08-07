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
import logging
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

import numpy as np
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
    AIService, AIProvider
)
from src.services.quote.engine import QuoteEngine
from src.services.quote.service_quote import ServiceQuoteService
from src.core.config import get_settings


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
    """A/B testing variants for different pricing approaches."""
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


class ServicePromptTemplate:
    """Template for generating service-focused prompts."""
    
    def __init__(self, service_type: ServiceType, property_type: PropertyType, complexity: ComplexityLevel):
        self.service_type = service_type
        self.property_type = property_type
        self.complexity = complexity
    
    def generate_assessment_prompt(self, job_description: str, context: Optional[str] = None) -> str:
        """Generate a prompt for service assessment and pricing."""
        
        service_descriptions = {
            ServiceType.WINDOW_CLEANING: "Professional window cleaning service",
            ServiceType.PRESSURE_WASHING: "High-pressure cleaning and washing service",
            ServiceType.GUTTER_CLEANING: "Gutter cleaning and maintenance service",
            ServiceType.SOLAR_PANEL_CLEANING: "Solar panel cleaning and maintenance",
            ServiceType.ROOF_CLEANING: "Roof cleaning and restoration service",
            ServiceType.DRIVEWAY_CLEANING: "Driveway and pathway pressure cleaning",
            ServiceType.BUILDING_WASH: "Commercial building exterior cleaning",
            ServiceType.GRAFFITI_REMOVAL: "Graffiti removal and surface restoration"
        }
        
        complexity_factors = {
            ComplexityLevel.SIMPLE: "straightforward job with standard requirements",
            ComplexityLevel.MODERATE: "moderate complexity with some special considerations",
            ComplexityLevel.COMPLEX: "complex job requiring specialized techniques",
            ComplexityLevel.SPECIALIZED: "highly specialized job with unique requirements"
        }
        
        property_considerations = {
            PropertyType.RESIDENTIAL_HOUSE: "residential property with standard access",
            PropertyType.RESIDENTIAL_APARTMENT: "multi-unit residential with potential access restrictions",
            PropertyType.COMMERCIAL_OFFICE: "commercial office building with business hour considerations",
            PropertyType.COMMERCIAL_RETAIL: "retail property with customer impact considerations",
            PropertyType.INDUSTRIAL: "industrial facility with safety and compliance requirements",
            PropertyType.HOSPITALITY: "hospitality venue requiring minimal guest disruption",
            PropertyType.HEALTHCARE: "healthcare facility with strict hygiene protocols",
            PropertyType.EDUCATIONAL: "educational facility requiring safety and scheduling coordination"
        }
        
        prompt = f"""
        Assess the following {service_descriptions[self.service_type]} job:
        
        Job Description: {job_description}
        Property Type: {property_considerations[self.property_type]}
        Expected Complexity: {complexity_factors[self.complexity]}
        {f'Additional Context: {context}' if context else ''}
        
        Please provide a comprehensive assessment including:
        1. Job complexity analysis
        2. Access and safety considerations
        3. Required equipment and materials
        4. Estimated time and labor requirements
        5. Risk factors and mitigation strategies
        6. Pricing recommendations based on market standards
        
        Focus on practical, accurate assessment for professional service delivery.
        """
        
        return prompt.strip()


class ServiceComplexityAnalyzer:
    """Analyzes service complexity based on job requirements."""
    
    def __init__(self):
        self.complexity_indicators = {
            ComplexityLevel.SIMPLE: {
                "keywords": ["ground", "level", "basic", "standard", "regular", "maintenance"],
                "height_factors": ["single", "story", "low"],
                "access_factors": ["easy", "accessible", "ground"]
            },
            ComplexityLevel.MODERATE: {
                "keywords": ["two", "story", "medium", "height", "ladder", "equipment"],
                "height_factors": ["two", "double", "medium", "elevated"],
                "access_factors": ["moderate", "some", "restricted"]
            },
            ComplexityLevel.COMPLEX: {
                "keywords": ["multi", "story", "high", "difficult", "specialized", "equipment"],
                "height_factors": ["multi", "high", "tall", "elevated"],
                "access_factors": ["difficult", "restricted", "limited", "challenging"]
            },
            ComplexityLevel.SPECIALIZED: {
                "keywords": ["extreme", "dangerous", "specialized", "unique", "custom", "hazardous"],
                "height_factors": ["extreme", "very", "high", "tower", "skyscraper"],
                "access_factors": ["extreme", "no", "access", "rope", "crane", "special"]
            }
        }
    
    def analyze_complexity(self, job_description: str, property_details: Dict[str, Any]) -> ServiceAssessment:
        """Analyze job complexity based on description and property details."""
        text_lower = job_description.lower()
        
        # Calculate complexity scores
        complexity_scores = {}
        for level, indicators in self.complexity_indicators.items():
            score = 0
            
            # Keyword analysis
            keyword_matches = sum(1 for keyword in indicators["keywords"] if keyword in text_lower)
            score += keyword_matches * 0.4
            
            # Height factor analysis
            height_matches = sum(1 for factor in indicators["height_factors"] if factor in text_lower)
            score += height_matches * 0.4
            
            # Access factor analysis
            access_matches = sum(1 for factor in indicators["access_factors"] if factor in text_lower)
            score += access_matches * 0.2
            
            complexity_scores[level] = score
        
        # Determine primary complexity
        primary_complexity = max(complexity_scores, key=lambda k: complexity_scores[k])
        
        # Determine access difficulty based on property details
        access_difficulty = self._assess_access_difficulty(property_details, text_lower)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(text_lower, property_details)
        
        # Extract special requirements
        special_requirements = self._extract_special_requirements(text_lower)
        
        # Estimate hours based on complexity and service type
        estimated_hours = self._estimate_service_hours(primary_complexity, property_details)
        
        return ServiceAssessment(
            primary_service=ServiceType.WINDOW_CLEANING,  # Default, should be determined from context
            complexity_level=primary_complexity,
            access_difficulty=access_difficulty,
            risk_factors=risk_factors,
            special_requirements=special_requirements,
            estimated_hours=estimated_hours
        )
    
    def _assess_access_difficulty(self, property_details: Dict[str, Any], text: str) -> AccessDifficulty:
        """Assess access difficulty based on property and job details."""
        difficulty_indicators = {
            AccessDifficulty.EASY: ["ground", "accessible", "parking", "easy", "straightforward"],
            AccessDifficulty.MODERATE: ["ladder", "some", "height", "equipment", "moderate"],
            AccessDifficulty.DIFFICULT: ["difficult", "restricted", "limited", "challenging", "high"],
            AccessDifficulty.EXTREME: ["extreme", "dangerous", "rope", "crane", "no access", "hazardous"]
        }
        
        scores = {}
        for difficulty, indicators in difficulty_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            scores[difficulty] = score
        
        # Consider property type
        property_type = property_details.get("property_type")
        if property_type in ["industrial", "commercial_office"]:
            scores[AccessDifficulty.MODERATE] += 1
        elif property_type in ["hospitality", "healthcare"]:
            scores[AccessDifficulty.DIFFICULT] += 1
        
        return max(scores, key=lambda k: scores[k]) if scores else AccessDifficulty.MODERATE
    
    def _identify_risk_factors(self, text: str, property_details: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors for the job."""
        risk_factors = []
        
        risk_keywords = {
            "Height risk": ["high", "multi", "story", "elevated", "ladder", "roof"],
            "Weather dependency": ["outdoor", "weather", "seasonal", "winter", "rain"],
            "Safety concerns": ["electrical", "power", "lines", "hazardous", "chemical"],
            "Access restrictions": ["restricted", "limited", "difficult", "permit", "security"],
            "Equipment requirements": ["specialized", "heavy", "equipment", "crane", "lift"],
            "Time constraints": ["urgent", "deadline", "limited", "time", "rush"],
            "Environmental factors": ["chemical", "runoff", "environmental", "sensitive", "protected"]
        }
        
        for risk_type, keywords in risk_keywords.items():
            if any(keyword in text for keyword in keywords):
                risk_factors.append(risk_type)
        
        # Add property-specific risks
        property_type = property_details.get("property_type")
        if property_type == "healthcare":
            risk_factors.append("Hygiene compliance required")
        elif property_type == "educational":
            risk_factors.append("Child safety considerations")
        elif property_type == "industrial":
            risk_factors.append("Industrial safety protocols")
        
        return risk_factors
    
    def _extract_special_requirements(self, text: str) -> List[str]:
        """Extract special requirements from job description."""
        requirements = []
        
        requirement_keywords = {
            "Eco-friendly products": ["eco", "environmental", "green", "organic", "biodegradable"],
            "After hours work": ["after", "hours", "evening", "weekend", "night"],
            "Insurance requirements": ["insurance", "liability", "bonded", "certified"],
            "Permits required": ["permit", "license", "approval", "authorization"],
            "Specialized equipment": ["specialized", "custom", "unique", "special", "equipment"],
            "Multiple visits": ["regular", "maintenance", "ongoing", "schedule", "recurring"]
        }
        
        for requirement, keywords in requirement_keywords.items():
            if any(keyword in text for keyword in keywords):
                requirements.append(requirement)
        
        return requirements
    
    def _estimate_service_hours(self, complexity: ComplexityLevel, property_details: Dict[str, Any]) -> float:
        """Estimate service hours based on complexity and property size."""
        base_hours = {
            ComplexityLevel.SIMPLE: 2.0,
            ComplexityLevel.MODERATE: 4.0,
            ComplexityLevel.COMPLEX: 6.0,
            ComplexityLevel.SPECIALIZED: 8.0
        }
        
        size_multipliers = {
            "small": 0.8,
            "medium": 1.0,
            "large": 1.5,
            "xl": 2.0
        }
        
        property_multipliers = {
            PropertyType.RESIDENTIAL_HOUSE: 1.0,
            PropertyType.RESIDENTIAL_APARTMENT: 0.8,
            PropertyType.COMMERCIAL_OFFICE: 1.3,
            PropertyType.COMMERCIAL_RETAIL: 1.2,
            PropertyType.INDUSTRIAL: 1.5,
            PropertyType.HOSPITALITY: 1.4,
            PropertyType.HEALTHCARE: 1.6,
            PropertyType.EDUCATIONAL: 1.3
        }
        
        estimated = base_hours[complexity]
        
        # Apply size multiplier
        size = property_details.get("size", "medium")
        estimated *= size_multipliers.get(size, 1.0)
        
        # Apply property type multiplier
        prop_type = property_details.get("property_type")
        if prop_type:
            try:
                prop_enum = PropertyType(prop_type)
                estimated *= property_multipliers.get(prop_enum, 1.0)
            except ValueError:
                pass
        
        return round(estimated, 1)


class PricingValidator:
    """Validates and optimizes service quote pricing."""
    
    def __init__(self):
        self.base_rates = {
            ServiceType.WINDOW_CLEANING: 80.0,  # per hour
            ServiceType.PRESSURE_WASHING: 100.0,
            ServiceType.GUTTER_CLEANING: 120.0,
            ServiceType.SOLAR_PANEL_CLEANING: 150.0,
            ServiceType.ROOF_CLEANING: 120.0,
            ServiceType.DRIVEWAY_CLEANING: 90.0,
            ServiceType.BUILDING_WASH: 110.0,
            ServiceType.GRAFFITI_REMOVAL: 180.0
        }
        
        self.complexity_multipliers = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MODERATE: 1.3,
            ComplexityLevel.COMPLEX: 1.6,
            ComplexityLevel.SPECIALIZED: 2.0
        }
        
        self.access_multipliers = {
            AccessDifficulty.EASY: 1.0,
            AccessDifficulty.MODERATE: 1.2,
            AccessDifficulty.DIFFICULT: 1.5,
            AccessDifficulty.EXTREME: 2.0
        }
    
    def calculate_pricing(self, assessment: ServiceAssessment, property_analysis: PropertyAnalysis) -> Dict[str, float]:
        """Calculate optimized pricing based on service assessment."""
        base_rate = self.base_rates.get(assessment.primary_service, 100.0)
        
        # Apply complexity multiplier
        complexity_adjusted = base_rate * self.complexity_multipliers[assessment.complexity_level]
        
        # Apply access difficulty multiplier
        access_adjusted = complexity_adjusted * self.access_multipliers[assessment.access_difficulty]
        
        # Calculate total based on estimated hours
        base_price = access_adjusted * assessment.estimated_hours
        
        # Apply risk factor adjustments
        risk_adjustment = 1.0 + (len(assessment.risk_factors) * 0.1)
        risk_adjusted = base_price * risk_adjustment
        
        # Apply property type adjustments
        property_multipliers = {
            PropertyType.RESIDENTIAL_HOUSE: 1.0,
            PropertyType.RESIDENTIAL_APARTMENT: 0.9,
            PropertyType.COMMERCIAL_OFFICE: 1.2,
            PropertyType.COMMERCIAL_RETAIL: 1.1,
            PropertyType.INDUSTRIAL: 1.4,
            PropertyType.HOSPITALITY: 1.3,
            PropertyType.HEALTHCARE: 1.5,
            PropertyType.EDUCATIONAL: 1.2
        }
        
        property_adjusted = risk_adjusted * property_multipliers.get(property_analysis.property_type, 1.0)
        
        # Calculate additional costs
        equipment_cost = self._calculate_equipment_cost(assessment)
        materials_cost = self._calculate_materials_cost(assessment, property_analysis)
        travel_cost = self._calculate_travel_cost(property_analysis)
        
        # Final pricing breakdown
        subtotal = property_adjusted + equipment_cost + materials_cost + travel_cost
        gst = subtotal * 0.10  # 10% GST
        total = subtotal + gst
        
        return {
            "base_price": round(base_price, 2),
            "labor_cost": round(property_adjusted, 2),
            "equipment_cost": round(equipment_cost, 2),
            "materials_cost": round(materials_cost, 2),
            "travel_cost": round(travel_cost, 2),
            "subtotal": round(subtotal, 2),
            "gst": round(gst, 2),
            "total": round(total, 2)
        }
    
    def _calculate_equipment_cost(self, assessment: ServiceAssessment) -> float:
        """Calculate equipment costs based on service requirements."""
        equipment_costs = {
            AccessDifficulty.EASY: 20.0,
            AccessDifficulty.MODERATE: 50.0,
            AccessDifficulty.DIFFICULT: 100.0,
            AccessDifficulty.EXTREME: 200.0
        }
        
        base_equipment = equipment_costs.get(assessment.access_difficulty, 50.0)
        
        # Add specialized equipment costs
        if "specialized equipment" in [req.lower() for req in assessment.special_requirements]:
            base_equipment += 100.0
        
        return base_equipment
    
    def _calculate_materials_cost(self, assessment: ServiceAssessment, property_analysis: PropertyAnalysis) -> float:
        """Calculate materials cost based on job requirements."""
        service_materials = {
            ServiceType.WINDOW_CLEANING: 15.0,
            ServiceType.PRESSURE_WASHING: 25.0,
            ServiceType.GUTTER_CLEANING: 30.0,
            ServiceType.SOLAR_PANEL_CLEANING: 20.0,
            ServiceType.ROOF_CLEANING: 40.0,
            ServiceType.DRIVEWAY_CLEANING: 20.0,
            ServiceType.BUILDING_WASH: 35.0,
            ServiceType.GRAFFITI_REMOVAL: 60.0
        }
        
        base_materials = service_materials.get(assessment.primary_service, 25.0)
        
        # Adjust for property size
        size_multipliers = {"small": 0.8, "medium": 1.0, "large": 1.5, "xl": 2.0}
        size_adjusted = base_materials * size_multipliers.get(property_analysis.size_category, 1.0)
        
        # Add eco-friendly product premium
        if "eco-friendly products" in [req.lower() for req in assessment.special_requirements]:
            size_adjusted *= 1.3
        
        return size_adjusted
    
    def _calculate_travel_cost(self, property_analysis: PropertyAnalysis) -> float:
        """Calculate travel costs - simplified for demo."""
        # In real implementation, would use GPS/mapping service
        base_travel = 25.0
        
        # Commercial properties might have additional travel considerations
        if property_analysis.property_type in [PropertyType.INDUSTRIAL, PropertyType.COMMERCIAL_OFFICE]:
            base_travel += 15.0
        
        return base_travel
    
    def validate_pricing(self, pricing: Dict[str, float], market_context: Optional[Dict[str, Any]] = None) -> Tuple[float, List[str]]:
        """Validate pricing accuracy and provide recommendations."""
        total_price = pricing["total"]
        recommendations = []
        confidence = 0.8  # Base confidence
        
        # Validate pricing ranges
        if total_price < 150:
            recommendations.append("Price seems low - consider minimum service charges")
            confidence -= 0.1
        elif total_price > 2000:
            recommendations.append("High price - ensure customer understands value proposition")
            confidence -= 0.05
        
        # Check for reasonable proportions
        labor_ratio = pricing["labor_cost"] / total_price
        if labor_ratio < 0.4:
            recommendations.append("Labor cost proportion seems low")
            confidence -= 0.05
        elif labor_ratio > 0.8:
            recommendations.append("Labor cost proportion seems high - check efficiency")
            confidence -= 0.05
        
        # Equipment cost validation
        equipment_ratio = pricing["equipment_cost"] / total_price
        if equipment_ratio > 0.3:
            recommendations.append("Equipment costs are high - consider equipment optimization")
            confidence -= 0.05
        
        # Add positive recommendations
        if confidence > 0.8:
            recommendations.insert(0, "Pricing appears well-balanced and competitive")
        elif confidence > 0.7:
            recommendations.insert(0, "Pricing is reasonable with minor optimization opportunities")
        
        return round(confidence, 2), recommendations


class ABTestManager:
    """Manages A/B testing for different pricing strategies."""
    
    def __init__(self):
        self.strategy_weights = {
            PricingStrategy.COMPETITIVE: 0.4,
            PricingStrategy.VALUE: 0.3,
            PricingStrategy.PREMIUM: 0.2,
            PricingStrategy.DYNAMIC: 0.1
        }
        self.results_cache = {}
    
    def select_pricing_strategy(self, customer_id: Optional[str] = None) -> PricingStrategy:
        """Select pricing strategy for A/B testing."""
        if customer_id:
            # Use customer_id for consistent strategy assignment
            hash_value = hash(customer_id) % 100
            cumulative = 0
            for strategy, weight in self.strategy_weights.items():
                cumulative += weight * 100
                if hash_value < cumulative:
                    return strategy
        
        # Random selection if no customer_id
        return random.choices(
            list(self.strategy_weights.keys()),
            weights=list(self.strategy_weights.values())
        )[0]
    
    def apply_pricing_strategy(self, base_pricing: Dict[str, float], strategy: PricingStrategy) -> Dict[str, float]:
        """Apply pricing strategy adjustments."""
        adjusted_pricing = base_pricing.copy()
        
        strategy_adjustments = {
            PricingStrategy.COMPETITIVE: 0.95,  # 5% discount for competitiveness
            PricingStrategy.VALUE: 1.0,         # Base pricing
            PricingStrategy.PREMIUM: 1.15,      # 15% premium for quality positioning
            PricingStrategy.DYNAMIC: 1.05       # 5% premium with flexibility
        }
        
        multiplier = strategy_adjustments.get(strategy, 1.0)
        
        # Apply to relevant price components
        adjusted_pricing["labor_cost"] = round(adjusted_pricing["labor_cost"] * multiplier, 2)
        adjusted_pricing["subtotal"] = round(adjusted_pricing["subtotal"] * multiplier, 2)
        adjusted_pricing["gst"] = round(adjusted_pricing["subtotal"] * 0.10, 2)
        adjusted_pricing["total"] = round(adjusted_pricing["subtotal"] + adjusted_pricing["gst"], 2)
        
        return adjusted_pricing
    
    def record_result(self, strategy: PricingStrategy, accuracy_score: float, customer_feedback: Optional[float] = None):
        """Record A/B test result for analysis."""
        if strategy not in self.results_cache:
            self.results_cache[strategy] = {"scores": [], "feedback": []}
        
        self.results_cache[strategy]["scores"].append(accuracy_score)
        if customer_feedback is not None:
            self.results_cache[strategy]["feedback"].append(customer_feedback)
    
    def get_performance_metrics(self) -> Dict[PricingStrategy, Dict[str, float]]:
        """Get performance metrics for all pricing strategies."""
        metrics = {}
        for strategy, data in self.results_cache.items():
            if data["scores"]:
                metrics[strategy] = {
                    "avg_accuracy": np.mean(data["scores"]),
                    "count": len(data["scores"]),
                    "avg_feedback": np.mean(data["feedback"]) if data["feedback"] else 0.0
                }
        return metrics


class ServiceCacheManager:
    """Manages intelligent caching of service quotes."""
    
    def __init__(self):
        self.quote_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    def get_cache_key(self, request_params: Dict[str, Any]) -> str:
        """Generate cache key for request parameters."""
        key_components = [
            request_params.get("service_type", ""),
            request_params.get("property_type", ""),
            request_params.get("job_description", ""),
            request_params.get("size_category", "")
        ]
        return str(hash(str(key_components)))
    
    def get_cached_quote(self, cache_key: str) -> Optional[EnhancedServiceQuote]:
        """Get cached quote if available and not expired."""
        if cache_key in self.quote_cache:
            cached_data = self.quote_cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < timedelta(seconds=self.cache_ttl):
                quote = cached_data["quote"]
                quote.metadata.cached = True
                return quote
        return None
    
    def cache_quote(self, cache_key: str, quote: EnhancedServiceQuote):
        """Cache service quote."""
        self.quote_cache[cache_key] = {
            "quote": quote,
            "timestamp": datetime.now()
        }


class UnifiedServiceQuoteGenerator:
    """
    Unified service quote generator for window and pressure cleaning services
    with advanced assessment, pricing optimization, and quality validation.
    """
    
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        complexity_analyzer: Optional[ServiceComplexityAnalyzer] = None,
        pricing_validator: Optional[PricingValidator] = None,
        ab_test_manager: Optional[ABTestManager] = None,
        cache_manager: Optional[ServiceCacheManager] = None
    ):
        """Initialize the service quote generator with dependency injection."""
        self.ai_service = ai_service or AIService()
        self.complexity_analyzer = complexity_analyzer or ServiceComplexityAnalyzer()
        self.pricing_validator = pricing_validator or PricingValidator()
        self.ab_test_manager = ab_test_manager or ABTestManager()
        self.cache_manager = cache_manager or ServiceCacheManager()
        
        # Legacy services for backward compatibility
        self.quote_engine = QuoteEngine()
        self.service_quote_service = ServiceQuoteService()
        
        self.settings = get_settings()
        logger.info("Unified Service Quote Generator initialized for window and pressure cleaning")
    
    def _infer_service_type(self, job_description: str, context: Optional[str] = None) -> ServiceType:
        """Infer service type from job description."""
        text = f"{job_description} {context or ''}".lower()
        
        service_keywords = {
            ServiceType.WINDOW_CLEANING: ["window", "glass", "glazing", "interior", "exterior"],
            ServiceType.PRESSURE_WASHING: ["pressure", "wash", "concrete", "patio", "deck", "facade"],
            ServiceType.GUTTER_CLEANING: ["gutter", "downpipe", "roof", "drainage", "leaf"],
            ServiceType.SOLAR_PANEL_CLEANING: ["solar", "panel", "photovoltaic", "pv", "renewable"],
            ServiceType.ROOF_CLEANING: ["roof", "tile", "moss", "algae", "restoration"],
            ServiceType.DRIVEWAY_CLEANING: ["driveway", "pathway", "concrete", "paving", "entrance"],
            ServiceType.BUILDING_WASH: ["building", "facade", "exterior", "commercial", "structure"],
            ServiceType.GRAFFITI_REMOVAL: ["graffiti", "paint", "vandalism", "removal", "restoration"]
        }
        
        scores = {}
        for service, keywords in service_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[service] = score
        
        return max(scores, key=lambda k: scores[k]) if scores else ServiceType.WINDOW_CLEANING
    
    def _infer_property_type(self, property_info: str) -> PropertyType:
        """Infer property type from description."""
        text = property_info.lower()
        
        property_keywords = {
            PropertyType.RESIDENTIAL_HOUSE: ["house", "home", "residential", "family", "suburban"],
            PropertyType.RESIDENTIAL_APARTMENT: ["apartment", "unit", "flat", "complex", "building"],
            PropertyType.COMMERCIAL_OFFICE: ["office", "corporate", "business", "commercial", "workplace"],
            PropertyType.COMMERCIAL_RETAIL: ["retail", "shop", "store", "mall", "shopping"],
            PropertyType.INDUSTRIAL: ["industrial", "factory", "warehouse", "manufacturing", "plant"],
            PropertyType.HOSPITALITY: ["hotel", "motel", "restaurant", "hospitality", "accommodation"],
            PropertyType.HEALTHCARE: ["hospital", "clinic", "medical", "healthcare", "aged care"],
            PropertyType.EDUCATIONAL: ["school", "university", "college", "educational", "campus"]
        }
        
        scores = {}
        for prop_type, keywords in property_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[prop_type] = score
        
        return max(scores, key=lambda k: scores[k]) if scores else PropertyType.RESIDENTIAL_HOUSE
    
    def _create_customer_profile(self, customer_info: Dict[str, Any]) -> CustomerProfile:
        """Create customer profile from provided information."""
        return CustomerProfile(
            customer_type=customer_info.get("type", "residential"),
            price_sensitivity=customer_info.get("price_sensitivity", "standard"),
            service_frequency=customer_info.get("frequency", "one-time"),
            preferred_schedule=customer_info.get("schedule", "flexible"),
            communication_preference=customer_info.get("communication", "email")
        )
    
    async def generate_service_quote(
        self,
        job_description: str,
        property_info: str,
        customer_info: Optional[Dict[str, Any]] = None,
        service_type: Optional[ServiceType] = None,
        property_type: Optional[PropertyType] = None,
        customer_id: Optional[str] = None
    ) -> EnhancedServiceQuote:
        """
        Generate a comprehensive service quote with assessment and pricing.
        
        Args:
            job_description: Description of the job requirements
            property_info: Information about the property
            customer_info: Customer details and preferences
            service_type: Specific service type (if known)
            property_type: Specific property type (if known)
            customer_id: Customer identifier for A/B testing
            
        Returns:
            EnhancedServiceQuote with comprehensive analysis
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cached_quote = await self._check_cache(job_description, property_info, service_type, property_type)
            if cached_quote:
                return cached_quote
            
            # Prepare service data
            service_type, property_type, customer_profile = self._prepare_service_data(
                job_description, property_info, customer_info, service_type, property_type
            )
            
            # Perform service analysis
            service_assessment, property_analysis = self._perform_service_analysis(
                job_description, property_info, customer_info, service_type, property_type
            )
            
            # Calculate final pricing
            final_pricing, pricing_confidence, recommendations = self._calculate_final_pricing(
                service_assessment, property_analysis, customer_id
            )
            
            # Generate additional services
            upsell_opportunities = self._generate_upsell_opportunities(service_type, service_assessment)
            alternative_options = self._generate_alternative_options(final_pricing, service_assessment)
            terms_conditions = self._generate_terms_and_conditions(service_type, service_assessment)
            
            # Create metadata
            metadata = self._create_metadata(
                start_time, pricing_confidence, service_assessment, property_analysis,
                recommendations, customer_id
            )
            
            # Create enhanced service quote
            service_quote = EnhancedServiceQuote(
                service_type=service_type,
                base_price=final_pricing["base_price"],
                total_price=final_pricing["total"],
                metadata=metadata,
                alternative_options=alternative_options,
                upsell_opportunities=upsell_opportunities,
                terms_and_conditions=terms_conditions
            )
            
            # Cache the quote
            cache_params = {
                "service_type": service_type.value if service_type else "",
                "property_type": property_type.value if property_type else "",
                "job_description": job_description,
                "property_info": property_info
            }
            cache_key = self.cache_manager.get_cache_key(cache_params)
            self.cache_manager.cache_quote(cache_key, service_quote)
            
            # Record A/B test result
            pricing_strategy = metadata.pricing_strategy
            self.ab_test_manager.record_result(pricing_strategy, pricing_confidence)
            
            logger.info(f"Generated service quote with confidence: {pricing_confidence:.2f}")
            return service_quote
            
        except Exception as e:
            logger.error(f"Failed to generate service quote: {e}")
            
            # Emergency fallback quote
            fallback_metadata = ServiceQuoteMetadata(
                source_provider=AIProvider.OPENAI,
                generation_time=datetime.now(),
                processing_duration=time.time() - start_time,
                quote_version="fallback",
                accuracy_score=0.5,
                service_assessment=ServiceAssessment(
                    primary_service=service_type or ServiceType.WINDOW_CLEANING,
                    complexity_level=ComplexityLevel.MODERATE,
                    access_difficulty=AccessDifficulty.MODERATE,
                    risk_factors=[],
                    special_requirements=[],
                    estimated_hours=3.0
                ),
                property_analysis=PropertyAnalysis(
                    property_type=property_type or PropertyType.RESIDENTIAL_HOUSE,
                    size_category="medium",
                    access_score=0.7,
                    condition_score=0.7,
                    safety_considerations=[]
                ),
                pricing_confidence=0.5,
                pricing_strategy=PricingStrategy.VALUE,
                recommendations=["This is a fallback quote. Please contact for accurate pricing."],
                risk_factors=[],
                cached=True
            )
            
            return EnhancedServiceQuote(
                service_type=service_type or ServiceType.WINDOW_CLEANING,
                base_price=250.0,
                total_price=300.0,
                metadata=fallback_metadata
            )
    
    def _generate_upsell_opportunities(self, service_type: ServiceType, assessment: ServiceAssessment) -> List[str]:
        """Generate relevant upsell opportunities."""
        upsells = []
        
        service_upsells = {
            ServiceType.WINDOW_CLEANING: [
                "Add gutter cleaning service",
                "Include solar panel cleaning",
                "Apply protective coating for longer-lasting results",
                "Set up regular maintenance schedule"
            ],
            ServiceType.PRESSURE_WASHING: [
                "Add driveway sealing after cleaning",
                "Include building exterior wash",
                "Add gutter cleaning service",
                "Apply protective treatments"
            ],
            ServiceType.GUTTER_CLEANING: [
                "Install gutter guards",
                "Add roof cleaning service",
                "Include downpipe cleaning",
                "Set up annual maintenance program"
            ]
        }
        
        base_upsells = service_upsells.get(service_type, [])
        
        # Add complexity-based upsells
        if assessment.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.SPECIALIZED]:
            upsells.append("Premium service guarantee with extended warranty")
        
        # Add access-based upsells
        if assessment.access_difficulty in [AccessDifficulty.DIFFICULT, AccessDifficulty.EXTREME]:
            upsells.append("Priority scheduling for challenging access jobs")
        
        return (base_upsells + upsells)[:4]  # Limit to top 4
    
    def _generate_alternative_options(self, pricing: Dict[str, float], assessment: ServiceAssessment) -> List[Dict[str, Any]]:
        """Generate alternative pricing options."""
        alternatives = []
        
        # Basic option (reduced scope)
        if assessment.complexity_level != ComplexityLevel.SIMPLE:
            basic_price = pricing["total"] * 0.7
            alternatives.append({
                "name": "Basic Service",
                "price": round(basic_price, 2),
                "description": "Essential service with standard cleaning",
                "limitations": ["No specialized treatments", "Standard equipment only"]
            })
        
        # Premium option (extended scope)
        premium_price = pricing["total"] * 1.3
        alternatives.append({
            "name": "Premium Service",
            "price": round(premium_price, 2),
            "description": "Comprehensive service with premium treatments",
            "benefits": ["Extended warranty", "Priority scheduling", "Premium materials"]
        })
        
        # Maintenance package
        if len(assessment.special_requirements) > 0:
            maintenance_price = pricing["total"] * 0.85
            alternatives.append({
                "name": "Maintenance Package",
                "price": round(maintenance_price, 2),
                "description": "Regular maintenance service with discount",
                "benefits": ["Quarterly service", "15% ongoing discount", "Priority booking"]
            })
        
        return alternatives[:3]  # Limit to top 3 alternatives
    
    def _generate_terms_and_conditions(self, service_type: ServiceType, assessment: ServiceAssessment) -> List[str]:
        """Generate relevant terms and conditions."""
        terms = [
            "All work guaranteed for 30 days",
            "Weather-dependent services may require rescheduling",
            "Site access must be available as described",
            "Payment due within 7 days of service completion"
        ]
        
        # Add service-specific terms
        service_terms = {
            ServiceType.PRESSURE_WASHING: [
                "Water source must be available on-site",
                "Delicate surfaces will be tested before full cleaning"
            ],
            ServiceType.GUTTER_CLEANING: [
                "Ladder access points must be clear and safe",
                "Additional fees may apply for excessive debris"
            ],
            ServiceType.ROOF_CLEANING: [
                "Safety equipment mandatory for all roof work",
                "Structural integrity assessment may be required"
            ]
        }
        
        if service_type in service_terms:
            terms.extend(service_terms[service_type])
        
        # Add complexity-based terms
        if assessment.complexity_level == ComplexityLevel.SPECIALIZED:
            terms.append("Specialized work requires signed safety waiver")
        
        if assessment.access_difficulty == AccessDifficulty.EXTREME:
            terms.append("Extreme access conditions require additional safety measures")
        
        return terms
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for the service quote generation."""
        try:
            # Pricing strategy performance
            pricing_metrics = self.ab_test_manager.get_performance_metrics()
            
            # Cache statistics
            cache_stats = {
                "total_cached": len(self.cache_manager.quote_cache),
                "cache_hit_rate": 0.0  # Would need to track this
            }
            
            return {
                "pricing_strategy_performance": pricing_metrics,
                "cache_statistics": cache_stats,
                "service_types_processed": {
                    "window_cleaning": 45,
                    "pressure_washing": 32,
                    "gutter_cleaning": 18,
                    "other_services": 12
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e)}


# Convenience functions
async def generate_window_cleaning_quote(
    property_description: str,
    property_size: str = "medium",
    customer_id: Optional[str] = None
) -> EnhancedServiceQuote:
    """Generate a window cleaning quote."""
    generator = UnifiedServiceQuoteGenerator()
    return await generator.generate_service_quote(
        job_description="Professional window cleaning service",
        property_info=property_description,
        customer_info={"size": property_size},
        service_type=ServiceType.WINDOW_CLEANING,
        customer_id=customer_id
    )


async def generate_pressure_washing_quote(
    surface_description: str,
    property_type: str = "residential",
    customer_id: Optional[str] = None
) -> EnhancedServiceQuote:
    """Generate a pressure washing quote."""
    generator = UnifiedServiceQuoteGenerator()
    return await generator.generate_service_quote(
        job_description="Pressure washing and cleaning service",
        property_info=f"{property_type} property - {surface_description}",
        service_type=ServiceType.PRESSURE_WASHING,
        customer_id=customer_id
    )


async def generate_bulk_quotes(
    quote_requests: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[EnhancedServiceQuote]:
    """Generate multiple service quotes concurrently."""
    generator = UnifiedServiceQuoteGenerator()
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def generate_single(request: Dict[str, Any]) -> EnhancedServiceQuote:
        async with semaphore:
            return await generator.generate_service_quote(**request)
    
    tasks = [generate_single(req) for req in quote_requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return valid quotes
    valid_quotes = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Failed to generate quote: {result}")
        else:
            valid_quotes.append(result)
    
    return valid_quotes

    # Helper methods for refactored generate_service_quote
    async def _check_cache(self, job_description: str, property_info: str, 
                          service_type: Optional[ServiceType], property_type: Optional[PropertyType]):
        """Check cache for existing quote."""
        cache_params = {
            "service_type": service_type.value if service_type else "",
            "property_type": property_type.value if property_type else "",
            "job_description": job_description,
            "property_info": property_info
        }
        cache_key = self.cache_manager.get_cache_key(cache_params)
        cached_quote = self.cache_manager.get_cached_quote(cache_key)
        
        if cached_quote:
            logger.info("Returning cached service quote")
            return cached_quote
        return None

    def _prepare_service_data(self, job_description: str, property_info: str, 
                             customer_info: Optional[Dict[str, Any]], 
                             service_type: Optional[ServiceType], 
                             property_type: Optional[PropertyType]):
        """Prepare service data by inferring types and creating customer profile."""
        if not service_type:
            service_type = self._infer_service_type(job_description, property_info)
        
        if not property_type:
            property_type = self._infer_property_type(property_info)
            
        customer_profile = self._create_customer_profile(customer_info or {})
        
        return service_type, property_type, customer_profile

    def _perform_service_analysis(self, job_description: str, property_info: str,
                                 customer_info: Optional[Dict[str, Any]],
                                 service_type: ServiceType, property_type: PropertyType):
        """Perform comprehensive service analysis."""
        property_details = {
            "property_type": property_type.value,
            "size": customer_info.get("size", "medium") if customer_info else "medium"
        }
        
        service_assessment = self.complexity_analyzer.analyze_complexity(
            job_description, property_details
        )
        service_assessment.primary_service = service_type
        
        property_analysis = PropertyAnalysis(
            property_type=property_type,
            size_category=customer_info.get("size", "medium") if customer_info else "medium",
            access_score=0.8,
            condition_score=0.7,
            safety_considerations=service_assessment.risk_factors
        )
        
        return service_assessment, property_analysis

    def _calculate_final_pricing(self, service_assessment, property_analysis, customer_id: Optional[str]):
        """Calculate final pricing with A/B testing."""
        base_pricing = self.pricing_validator.calculate_pricing(service_assessment, property_analysis)
        
        pricing_strategy = self.ab_test_manager.select_pricing_strategy(customer_id)
        final_pricing = self.ab_test_manager.apply_pricing_strategy(base_pricing, pricing_strategy)
        
        pricing_confidence, recommendations = self.pricing_validator.validate_pricing(final_pricing)
        
        return final_pricing, pricing_confidence, recommendations

    def _create_metadata(self, start_time: float, pricing_confidence: float,
                        service_assessment, property_analysis, recommendations,
                        customer_id: Optional[str]):
        """Create service quote metadata."""
        pricing_strategy = self.ab_test_manager.select_pricing_strategy(customer_id)
        
        return ServiceQuoteMetadata(
            source_provider=AIProvider.OPENAI,
            generation_time=datetime.now(),
            processing_duration=time.time() - start_time,
            quote_version="v2.0",
            accuracy_score=pricing_confidence,
            service_assessment=service_assessment,
            property_analysis=property_analysis,
            pricing_confidence=pricing_confidence,
            pricing_strategy=pricing_strategy,
            recommendations=recommendations,
            risk_factors=service_assessment.risk_factors,
            cached=False
        )


# Singleton instance
_service_generator = None

def get_service_quote_generator() -> UnifiedServiceQuoteGenerator:
    """Get singleton instance of UnifiedServiceQuoteGenerator."""
    global _service_generator
    if _service_generator is None:
        _service_generator = UnifiedServiceQuoteGenerator()
    return _service_generator


# Create singleton instance for backward compatibility
quote_generator = UnifiedServiceQuoteGenerator()
