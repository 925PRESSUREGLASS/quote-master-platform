"""
Agent type definitions and role specifications for multi-agent AI system.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class AgentRole(str, Enum):
    """Specialized agent roles for different AI tasks."""
    
    # Core quote generation agents
    QUOTE_ANALYST = "quote_analyst"          # Analyze requirements and complexity
    CONTENT_CREATOR = "content_creator"       # Generate quote content
    QUALITY_REVIEWER = "quality_reviewer"    # Review and improve output
    
    # Specialized service agents  
    VOICE_PROCESSOR = "voice_processor"      # Handle voice-to-text workflows
    PSYCHOLOGY_ANALYZER = "psychology_analyzer"  # Psychological profile analysis
    PRICING_OPTIMIZER = "pricing_optimizer"  # Optimize pricing strategies
    
    # System optimization agents
    TOKEN_OPTIMIZER = "token_optimizer"      # Optimize API token usage
    COST_MONITOR = "cost_monitor"           # Monitor and optimize costs
    PERFORMANCE_TUNER = "performance_tuner" # Optimize response times
    
    # Workflow coordination agents
    WORKFLOW_COORDINATOR = "workflow_coordinator"  # Coordinate multi-agent tasks
    FALLBACK_HANDLER = "fallback_handler"    # Handle service failures
    CACHE_MANAGER = "cache_manager"         # Intelligent caching decisions
    
    # Code generation and development agents
    CODE_GENERATOR = "code_generator"       # Generate code from requirements
    CODE_REVIEWER = "code_reviewer"         # Review and improve code quality
    API_INTEGRATOR = "api_integrator"       # Handle API integration tasks


class AgentCapability(str, Enum):
    """Capabilities that agents can possess."""
    
    # Text processing capabilities
    TEXT_GENERATION = "text_generation"
    TEXT_ANALYSIS = "text_analysis"
    TEXT_SUMMARIZATION = "text_summarization"
    TEXT_CLASSIFICATION = "text_classification"
    
    # Specialized capabilities
    VOICE_TRANSCRIPTION = "voice_transcription"
    EMOTIONAL_ANALYSIS = "emotional_analysis"
    COST_OPTIMIZATION = "cost_optimization"
    QUALITY_SCORING = "quality_scoring"
    
    # System capabilities
    CACHING = "caching"
    MONITORING = "monitoring"
    ROUTING = "routing"
    FALLBACK_HANDLING = "fallback_handling"
    
    # Code generation capabilities
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_DEBUGGING = "code_debugging"
    API_DEVELOPMENT = "api_development"
    DATABASE_INTEGRATION = "database_integration"
    UNIT_TESTING = "unit_testing"


class TaskComplexity(str, Enum):
    """Task complexity levels for optimal provider selection."""
    
    SIMPLE = "simple"        # Basic tasks - use cheaper models
    MODERATE = "moderate"    # Standard tasks - use balanced models  
    COMPLEX = "complex"      # Advanced tasks - use premium models
    CRITICAL = "critical"    # Mission-critical - use best available


class ProviderTier(str, Enum):
    """Provider tiers based on cost and capability."""
    
    ECONOMY = "economy"      # Low cost, basic capability (GPT-4o mini)
    STANDARD = "standard"    # Balanced cost/performance (Claude Haiku)
    PREMIUM = "premium"      # High capability (GPT-4, Claude Sonnet)
    FLAGSHIP = "flagship"    # Best available (GPT-5, o3-pro when available)


@dataclass
class AgentContext:
    """Context information for agent execution."""
    
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    task_complexity: TaskComplexity = TaskComplexity.MODERATE
    max_tokens: int = 500
    temperature: float = 0.7
    budget_limit: Optional[float] = None
    quality_threshold: float = 0.7
    response_time_limit: Optional[float] = None
    preferred_provider: Optional[str] = None
    cache_enabled: bool = True
    fallback_enabled: bool = True
    
    # Workflow tracking
    workflow_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Metadata
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentCapabilityMap:
    """Maps agent roles to their capabilities and optimal providers."""
    
    role: AgentRole
    capabilities: List[AgentCapability]
    optimal_providers: List[ProviderTier]
    token_efficiency: float  # 0-1 scale
    cost_efficiency: float   # 0-1 scale
    quality_rating: float    # 0-1 scale
    specialization_score: float  # 0-1 scale


# Pre-defined agent capability mappings
AGENT_CAPABILITIES: Dict[AgentRole, AgentCapabilityMap] = {
    
    AgentRole.QUOTE_ANALYST: AgentCapabilityMap(
        role=AgentRole.QUOTE_ANALYST,
        capabilities=[
            AgentCapability.TEXT_ANALYSIS,
            AgentCapability.TEXT_CLASSIFICATION,
            AgentCapability.QUALITY_SCORING
        ],
        optimal_providers=[ProviderTier.STANDARD, ProviderTier.ECONOMY],
        token_efficiency=0.9,
        cost_efficiency=0.8,
        quality_rating=0.7,
        specialization_score=0.8
    ),
    
    AgentRole.CONTENT_CREATOR: AgentCapabilityMap(
        role=AgentRole.CONTENT_CREATOR,
        capabilities=[
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TEXT_ANALYSIS
        ],
        optimal_providers=[ProviderTier.PREMIUM, ProviderTier.FLAGSHIP],
        token_efficiency=0.7,
        cost_efficiency=0.6,
        quality_rating=0.9,
        specialization_score=0.9
    ),
    
    AgentRole.QUALITY_REVIEWER: AgentCapabilityMap(
        role=AgentRole.QUALITY_REVIEWER,
        capabilities=[
            AgentCapability.TEXT_ANALYSIS,
            AgentCapability.QUALITY_SCORING,
            AgentCapability.TEXT_CLASSIFICATION
        ],
        optimal_providers=[ProviderTier.STANDARD, ProviderTier.PREMIUM],
        token_efficiency=0.8,
        cost_efficiency=0.7,
        quality_rating=0.8,
        specialization_score=0.8
    ),
    
    AgentRole.VOICE_PROCESSOR: AgentCapabilityMap(
        role=AgentRole.VOICE_PROCESSOR,
        capabilities=[
            AgentCapability.VOICE_TRANSCRIPTION,
            AgentCapability.TEXT_ANALYSIS,
            AgentCapability.EMOTIONAL_ANALYSIS
        ],
        optimal_providers=[ProviderTier.STANDARD],  # Whisper is standard tier
        token_efficiency=0.9,
        cost_efficiency=0.9,
        quality_rating=0.8,
        specialization_score=1.0
    ),
    
    AgentRole.PSYCHOLOGY_ANALYZER: AgentCapabilityMap(
        role=AgentRole.PSYCHOLOGY_ANALYZER,
        capabilities=[
            AgentCapability.EMOTIONAL_ANALYSIS,
            AgentCapability.TEXT_ANALYSIS,
            AgentCapability.TEXT_CLASSIFICATION
        ],
        optimal_providers=[ProviderTier.PREMIUM, ProviderTier.FLAGSHIP],
        token_efficiency=0.6,
        cost_efficiency=0.5,
        quality_rating=0.9,
        specialization_score=0.9
    ),
    
    AgentRole.TOKEN_OPTIMIZER: AgentCapabilityMap(
        role=AgentRole.TOKEN_OPTIMIZER,
        capabilities=[
            AgentCapability.COST_OPTIMIZATION,
            AgentCapability.ROUTING,
            AgentCapability.MONITORING
        ],
        optimal_providers=[ProviderTier.ECONOMY],  # Lightweight optimization
        token_efficiency=1.0,
        cost_efficiency=1.0,
        quality_rating=0.6,
        specialization_score=1.0
    ),
    
    AgentRole.WORKFLOW_COORDINATOR: AgentCapabilityMap(
        role=AgentRole.WORKFLOW_COORDINATOR,
        capabilities=[
            AgentCapability.ROUTING,
            AgentCapability.MONITORING,
            AgentCapability.FALLBACK_HANDLING
        ],
        optimal_providers=[ProviderTier.STANDARD],
        token_efficiency=0.9,
        cost_efficiency=0.8,
        quality_rating=0.7,
        specialization_score=0.8
    ),
    
    AgentRole.CACHE_MANAGER: AgentCapabilityMap(
        role=AgentRole.CACHE_MANAGER,
        capabilities=[
            AgentCapability.CACHING,
            AgentCapability.MONITORING,
            AgentCapability.COST_OPTIMIZATION
        ],
        optimal_providers=[ProviderTier.ECONOMY],  # Lightweight decisions
        token_efficiency=1.0,
        cost_efficiency=0.9,
        quality_rating=0.6,
        specialization_score=0.9
    ),
    
    AgentRole.CODE_GENERATOR: AgentCapabilityMap(
        role=AgentRole.CODE_GENERATOR,
        capabilities=[
            AgentCapability.CODE_GENERATION,
            AgentCapability.API_DEVELOPMENT,
            AgentCapability.DATABASE_INTEGRATION,
            AgentCapability.UNIT_TESTING
        ],
        optimal_providers=[ProviderTier.PREMIUM, ProviderTier.FLAGSHIP],  # Codex models
        token_efficiency=0.6,
        cost_efficiency=0.5,
        quality_rating=0.9,
        specialization_score=1.0
    ),
    
    AgentRole.CODE_REVIEWER: AgentCapabilityMap(
        role=AgentRole.CODE_REVIEWER,
        capabilities=[
            AgentCapability.CODE_REVIEW,
            AgentCapability.CODE_DEBUGGING,
            AgentCapability.QUALITY_SCORING,
            AgentCapability.TEXT_ANALYSIS
        ],
        optimal_providers=[ProviderTier.PREMIUM, ProviderTier.STANDARD],
        token_efficiency=0.8,
        cost_efficiency=0.7,
        quality_rating=0.9,
        specialization_score=0.9
    ),
    
    AgentRole.API_INTEGRATOR: AgentCapabilityMap(
        role=AgentRole.API_INTEGRATOR,
        capabilities=[
            AgentCapability.API_DEVELOPMENT,
            AgentCapability.CODE_GENERATION,
            AgentCapability.DATABASE_INTEGRATION,
            AgentCapability.TEXT_ANALYSIS
        ],
        optimal_providers=[ProviderTier.STANDARD, ProviderTier.PREMIUM],
        token_efficiency=0.7,
        cost_efficiency=0.6,
        quality_rating=0.8,
        specialization_score=0.8
    ),
}


# Provider-to-model mapping for easy updates when new models are available
PROVIDER_MODEL_MAPPING: Dict[ProviderTier, Dict[str, str]] = {
    
    ProviderTier.ECONOMY: {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "azure": "gpt-4o-mini"
    },
    
    ProviderTier.STANDARD: {
        "openai": "gpt-4o", 
        "anthropic": "claude-3-sonnet-20240229",
        "azure": "gpt-4o"
    },
    
    ProviderTier.PREMIUM: {
        "openai": "gpt-4-turbo",
        "anthropic": "claude-3-opus-20240229", 
        "azure": "gpt-4-turbo",
        "codex": "code-davinci-002"  # Codex for code generation
    },
    
    ProviderTier.FLAGSHIP: {
        "openai": "gpt-5",  # When available
        "openai_reasoning": "o3-pro",  # When available
        "anthropic": "claude-3-opus-20240229",  # Current flagship
        "azure": "gpt-5"  # When available
    }
}


def get_optimal_provider(agent_role: AgentRole, task_complexity: TaskComplexity) -> ProviderTier:
    """Get the optimal provider tier for an agent role and task complexity."""
    
    agent_map = AGENT_CAPABILITIES.get(agent_role)
    if not agent_map:
        return ProviderTier.STANDARD  # Default fallback
    
    # Adjust provider tier based on task complexity
    optimal_tiers = agent_map.optimal_providers
    
    if task_complexity == TaskComplexity.CRITICAL:
        return ProviderTier.FLAGSHIP
    elif task_complexity == TaskComplexity.COMPLEX:
        return max(optimal_tiers, default=ProviderTier.PREMIUM)
    elif task_complexity == TaskComplexity.SIMPLE:
        return min(optimal_tiers, default=ProviderTier.ECONOMY)
    else:  # MODERATE
        return optimal_tiers[0] if optimal_tiers else ProviderTier.STANDARD