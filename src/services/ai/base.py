"""Base AI service class and common utilities."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class AIModelType(str, Enum):
    """AI model types."""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35 = "openai_gpt35"
    CLAUDE_SONNET = "claude_sonnet"
    CLAUDE_HAIKU = "claude_haiku"
    CLAUDE_OPUS = "claude_opus"


class AITaskType(str, Enum):
    """AI task types."""
    QUOTE_GENERATION = "quote_generation"
    TEXT_ANALYSIS = "text_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    PSYCHOLOGY_ANALYSIS = "psychology_analysis"
    TRANSCRIPTION = "transcription"
    CONTENT_MODERATION = "content_moderation"
    TRANSLATION = "translation"


@dataclass
class AIResponse:
    """Standardized AI service response."""
    success: bool
    content: str
    model_used: str
    task_type: AITaskType
    metadata: Dict[str, Any]
    usage: Dict[str, Any]
    processing_time: float
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    
    def __post_init__(self):
        """Validate response after initialization."""
        if not self.success and not self.error_message:
            raise ValueError("Failed responses must include an error message")


@dataclass
class AIRequest:
    """Standardized AI service request."""
    task_type: AITaskType
    prompt: str
    context: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    model_preference: Optional[AIModelType] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.parameters is None:
            self.parameters = {}
        
        if self.max_tokens is None:
            self.max_tokens = 1000
        
        if self.temperature is None:
            self.temperature = 0.7


class AIServiceBase(ABC):
    """Base class for AI services."""
    
    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self._client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the AI service client."""
        pass
    
    @abstractmethod
    async def _make_request(self, request: AIRequest) -> AIResponse:
        """Make a request to the AI service."""
        pass
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using the AI service."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting AI request: {request.task_type} with model {self.model_name}")
            
            # Validate request
            self._validate_request(request)
            
            # Make the actual request
            response = await self._make_request(request)
            
            # Update processing time
            response.processing_time = time.time() - start_time
            
            logger.info(f"AI request completed in {response.processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"AI request failed after {processing_time:.2f}s: {str(e)}")
            
            return AIResponse(
                success=False,
                content="",
                model_used=self.model_name,
                task_type=request.task_type,
                metadata={},
                usage={},
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _validate_request(self, request: AIRequest) -> None:
        """Validate the AI request."""
        if not request.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if request.max_tokens and request.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if request.temperature and (request.temperature < 0 or request.temperature > 2):
            raise ValueError("temperature must be between 0 and 2")
    
    def _build_prompt(self, request: AIRequest) -> str:
        """Build the complete prompt for the AI service."""
        prompt_parts = []
        
        # Add context if provided
        if request.context:
            prompt_parts.append(f"Context: {request.context}")
        
        # Add task-specific instructions
        task_instructions = self._get_task_instructions(request.task_type)
        if task_instructions:
            prompt_parts.append(task_instructions)
        
        # Add the main prompt
        prompt_parts.append(request.prompt)
        
        return "\n\n".join(prompt_parts)
    
    def _get_task_instructions(self, task_type: AITaskType) -> str:
        """Get task-specific instructions."""
        instructions = {
            AITaskType.QUOTE_GENERATION: (
                "You are an expert quote generator. Create inspirational, meaningful, "
                "and thought-provoking quotes that resonate with people. Focus on clarity, "
                "wisdom, and emotional impact. Ensure the quote is original and well-crafted."
            ),
            AITaskType.TEXT_ANALYSIS: (
                "You are a text analysis expert. Analyze the given text for key themes, "
                "sentiment, style, and meaning. Provide detailed insights and observations."
            ),
            AITaskType.SENTIMENT_ANALYSIS: (
                "Analyze the sentiment of the given text. Provide a sentiment score "
                "between -1 (very negative) and 1 (very positive), along with reasoning."
            ),
            AITaskType.PSYCHOLOGY_ANALYSIS: (
                "You are a psychology expert. Analyze the psychological aspects of the "
                "given text, including emotional patterns, cognitive frameworks, and "
                "psychological insights that could be valuable for personal development."
            ),
            AITaskType.CONTENT_MODERATION: (
                "You are a content moderator. Analyze the given content for any "
                "inappropriate, harmful, or offensive material. Consider context and intent."
            ),
            AITaskType.TRANSLATION: (
                "You are a professional translator. Provide accurate and natural "
                "translations while preserving the original meaning and tone."
            )
        }
        
        return instructions.get(task_type, "")
    
    def _extract_usage_info(self, response_data: Any) -> Dict[str, Any]:
        """Extract usage information from API response."""
        # Default implementation - should be overridden by specific services
        return {
            "tokens_used": 0,
            "cost_estimate": 0.0
        }
    
    def _calculate_confidence_score(self, response_data: Any, request: AIRequest) -> float:
        """Calculate a confidence score for the response."""
        # Default implementation - should be overridden by specific services
        # This is a simplified scoring based on response length and request complexity
        
        response_length = len(response_data) if isinstance(response_data, str) else 0
        prompt_length = len(request.prompt)
        
        # Simple heuristic: longer, more detailed responses typically indicate higher confidence
        if response_length > prompt_length * 2:
            return 0.9
        elif response_length > prompt_length:
            return 0.7
        else:
            return 0.5
    
    async def health_check(self) -> bool:
        """Check if the AI service is healthy and responsive."""
        try:
            test_request = AIRequest(
                task_type=AITaskType.TEXT_ANALYSIS,
                prompt="Test prompt for health check",
                max_tokens=10,
                temperature=0.1
            )
            
            response = await self._make_request(test_request)
            return response.success
            
        except Exception as e:
            logger.error(f"Health check failed for {self.model_name}: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            "name": self.model_name,
            "type": self.__class__.__name__,
            "api_base": self.base_url,
            "capabilities": self._get_capabilities()
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get the capabilities of this AI service."""
        return [
            "text_generation",
            "text_analysis",
            "question_answering"
        ]


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    
    def __init__(self, message: str, service_name: str, error_code: Optional[str] = None):
        self.message = message
        self.service_name = service_name
        self.error_code = error_code
        super().__init__(self.message)


class AIServiceTimeoutError(AIServiceError):
    """Exception for AI service timeout errors."""
    pass


class AIServiceQuotaError(AIServiceError):
    """Exception for AI service quota/rate limit errors."""
    pass


class AIServiceContentError(AIServiceError):
    """Exception for AI service content policy errors."""
    pass


def format_prompt_for_quotes(
    base_prompt: str,
    style: Optional[str] = None,
    tone: Optional[str] = None,
    length: Optional[str] = None,
    author_style: Optional[str] = None,
    context: Optional[str] = None
) -> str:
    """Format a prompt specifically for quote generation."""
    
    prompt_parts = [
        "Generate an inspirational quote based on the following requirements:"
    ]
    
    # Add the base prompt/topic
    prompt_parts.append(f"Topic/Theme: {base_prompt}")
    
    # Add style requirements
    if style:
        prompt_parts.append(f"Style: {style}")
    
    if tone:
        prompt_parts.append(f"Tone: {tone}")
    
    if length:
        length_mapping = {
            "short": "Keep it concise (under 20 words)",
            "medium": "Medium length (20-50 words)",
            "long": "Longer format (50+ words, can be multiple sentences)"
        }
        prompt_parts.append(length_mapping.get(length, "Medium length"))
    
    if author_style:
        prompt_parts.append(f"Write in the style of: {author_style}")
    
    if context:
        prompt_parts.append(f"Context/Situation: {context}")
    
    # Add specific instructions
    prompt_parts.extend([
        "",
        "Requirements:",
        "- Create an original, meaningful quote",
        "- Make it inspiring and thought-provoking",
        "- Ensure clarity and emotional impact",
        "- Return only the quote text without attribution or quotes",
        "- Make it memorable and shareable"
    ])
    
    return "\n".join(prompt_parts)


def format_prompt_for_analysis(
    text: str,
    analysis_type: str = "comprehensive"
) -> str:
    """Format a prompt for text analysis."""
    
    analysis_instructions = {
        "sentiment": "Analyze the sentiment and emotional tone of this text.",
        "psychology": "Provide psychological insights about this text, including emotional patterns and cognitive frameworks.",
        "comprehensive": "Provide a comprehensive analysis including sentiment, themes, style, and psychological insights.",
        "themes": "Identify the main themes and concepts in this text.",
        "style": "Analyze the writing style, tone, and literary techniques used."
    }
    
    instruction = analysis_instructions.get(analysis_type, analysis_instructions["comprehensive"])
    
    return f"""{instruction}

Text to analyze:
{text}

Please provide a detailed analysis with specific observations and insights."""