"""Anthropic Claude service implementation for Quote Master Pro."""

import anthropic
from typing import Dict, Any, Optional
import logging
import asyncio

from .base import AIServiceBase, AIRequest, AIResponse, AITaskType, AIServiceError, AIServiceTimeoutError
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ClaudeService(AIServiceBase):
    """Anthropic Claude service implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 30
    ):
        self.timeout = timeout
        api_key = api_key or settings.anthropic_api_key
        model_name = model_name or settings.anthropic_model
        
        super().__init__(api_key=api_key, model_name=model_name)
    
    def _initialize_client(self) -> None:
        """Initialize Anthropic Claude client."""
        try:
            self._client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Claude client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {str(e)}")
            raise AIServiceError(f"Failed to initialize Claude: {str(e)}", "Claude")
    
    async def _make_request(self, request: AIRequest) -> AIResponse:
        """Make a request to Claude API."""
        
        try:
            # Build the complete prompt
            full_prompt = self._build_claude_prompt(request)
            
            # Prepare request parameters
            request_params = {
                "model": self.model_name,
                "max_tokens": request.max_tokens or settings.anthropic_max_tokens,
                "temperature": request.temperature or 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            }
            
            # Add system message if available
            system_message = self._get_system_message(request.task_type)
            if system_message:
                request_params["system"] = system_message
            
            # Add additional parameters from request
            if request.parameters:
                request_params.update(self._filter_claude_params(request.parameters))
            
            # Make the API call with timeout
            response = await asyncio.wait_for(
                self._make_claude_request(request_params),
                timeout=self.timeout
            )
            
            # Extract the generated content
            content = response.content[0].text.strip()
            
            # Extract usage information
            usage_info = self._extract_usage_info(response)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(response, request)
            
            # Build metadata
            metadata = {
                "model": response.model,
                "stop_reason": response.stop_reason,
                "response_id": response.id,
                "role": response.role
            }
            
            return AIResponse(
                success=True,
                content=content,
                model_used=self.model_name,
                task_type=request.task_type,
                metadata=metadata,
                usage=usage_info,
                processing_time=0.0,  # Will be set by parent class
                confidence_score=confidence
            )
            
        except asyncio.TimeoutError:
            raise AIServiceTimeoutError(
                f"Claude request timed out after {self.timeout} seconds",
                "Claude"
            )
        except anthropic.RateLimitError as e:
            raise AIServiceError(
                f"Claude rate limit exceeded: {str(e)}",
                "Claude",
                "RATE_LIMIT"
            )
        except anthropic.BadRequestError as e:
            raise AIServiceError(
                f"Invalid Claude request: {str(e)}",
                "Claude",
                "INVALID_REQUEST"
            )
        except anthropic.AuthenticationError as e:
            raise AIServiceError(
                f"Claude authentication failed: {str(e)}",
                "Claude",
                "AUTH_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected Claude error: {str(e)}")
            raise AIServiceError(
                f"Unexpected Claude error: {str(e)}",
                "Claude",
                "UNKNOWN_ERROR"
            )
    
    async def _make_claude_request(self, params: Dict[str, Any]):
        """Make the actual Claude API request."""
        # Run the synchronous Claude API call in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(**params)
        )
    
    def _build_claude_prompt(self, request: AIRequest) -> str:
        """Build Claude-specific prompt format."""
        
        prompt_parts = []
        
        # Add context if provided
        if request.context:
            prompt_parts.append(f"Context: {request.context}")
        
        # Add task-specific instructions for Claude
        task_instructions = self._get_claude_task_instructions(request.task_type)
        if task_instructions:
            prompt_parts.append(task_instructions)
        
        # Add the main prompt
        prompt_parts.append(request.prompt)
        
        # Add Claude-specific formatting instructions
        prompt_parts.append(
            "\nPlease provide your response clearly and concisely. "
            "Focus on quality and helpfulness."
        )
        
        return "\n\n".join(prompt_parts)
    
    def _get_system_message(self, task_type: AITaskType) -> str:
        """Get system message for different task types."""
        
        system_messages = {
            AITaskType.QUOTE_GENERATION: (
                "You are an expert quote generator with deep knowledge of wisdom literature, "
                "philosophy, and human nature. Your goal is to create original, meaningful quotes "
                "that inspire and resonate with people. Focus on clarity, depth, and emotional impact."
            ),
            AITaskType.TEXT_ANALYSIS: (
                "You are a skilled text analyst with expertise in literature, psychology, and "
                "communication. Provide thorough, insightful analysis that reveals deeper meanings "
                "and patterns in text."
            ),
            AITaskType.SENTIMENT_ANALYSIS: (
                "You are an expert in emotional intelligence and sentiment analysis. Analyze text "
                "for emotional content, tone, and underlying feelings with precision and nuance."
            ),
            AITaskType.PSYCHOLOGY_ANALYSIS: (
                "You are a psychology expert specializing in textual analysis. Identify psychological "
                "patterns, emotional intelligence insights, and personal development opportunities "
                "with professional expertise."
            ),
            AITaskType.CONTENT_MODERATION: (
                "You are a thoughtful content moderator who evaluates text for appropriateness "
                "while considering context, intent, and cultural sensitivity."
            )
        }
        
        return system_messages.get(
            task_type,
            "You are Claude, a helpful AI assistant created by Anthropic to be helpful, harmless, and honest."
        )
    
    def _get_claude_task_instructions(self, task_type: AITaskType) -> str:
        """Get Claude-specific task instructions."""
        
        instructions = {
            AITaskType.QUOTE_GENERATION: (
                "Create an original quote that:\n"
                "- Is inspiring and thought-provoking\n"
                "- Uses clear, accessible language\n"
                "- Conveys wisdom or insight\n"
                "- Is memorable and shareable\n"
                "- Avoids clichés while being relatable\n"
                "- Provides genuine value to the reader"
            ),
            AITaskType.PSYCHOLOGY_ANALYSIS: (
                "Provide psychological insights including:\n"
                "- Emotional patterns and themes\n"
                "- Cognitive frameworks evident in the text\n"
                "- Potential personality traits or mindsets\n"
                "- Growth opportunities or development areas\n"
                "- Psychological principles at play"
            ),
            AITaskType.SENTIMENT_ANALYSIS: (
                "Analyze sentiment by providing:\n"
                "- Overall sentiment score (-1 to 1)\n"
                "- Emotional tone and mood\n"
                "- Intensity of feelings expressed\n"
                "- Mixed emotions if present\n"
                "- Contextual factors affecting sentiment"
            )
        }
        
        return instructions.get(task_type, "")
    
    def _filter_claude_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and validate parameters for Claude API."""
        
        # List of valid Claude parameters
        valid_params = {
            'temperature', 'max_tokens', 'top_p', 'top_k', 'stop_sequences'
        }
        
        filtered = {}
        for k, v in params.items():
            if k in valid_params:
                # Convert stop_sequences for Claude if needed
                if k == 'stop_sequences' and isinstance(v, str):
                    filtered[k] = [v]
                else:
                    filtered[k] = v
        
        return filtered
    
    def _extract_usage_info(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from Claude response."""
        
        usage = getattr(response, 'usage', None)
        
        if usage:
            input_tokens = getattr(usage, 'input_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0)
            total_tokens = input_tokens + output_tokens
            
            # Rough pricing estimates for Claude (update with current pricing)
            cost_per_1k_input = 0.008  # Claude-3 Sonnet pricing
            cost_per_1k_output = 0.024
            
            estimated_cost = (
                (input_tokens / 1000) * cost_per_1k_input +
                (output_tokens / 1000) * cost_per_1k_output
            )
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": round(estimated_cost, 6)
            }
        
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }
    
    def _calculate_confidence_score(self, response: Any, request: AIRequest) -> float:
        """Calculate confidence score for Claude response."""
        
        stop_reason = getattr(response, 'stop_reason', None)
        content_length = len(response.content[0].text) if response.content else 0
        
        # Base confidence based on stop reason
        if stop_reason == "end_turn":
            base_confidence = 0.95
        elif stop_reason == "max_tokens":
            base_confidence = 0.75  # Truncated due to length
        elif stop_reason == "stop_sequence":
            base_confidence = 0.9   # Stopped at requested sequence
        else:
            base_confidence = 0.6
        
        # Adjust based on content quality indicators
        if content_length > 50:  # Reasonable response length
            length_factor = 1.0
        elif content_length > 20:
            length_factor = 0.9
        else:
            length_factor = 0.7
        
        # Claude tends to provide well-structured responses
        structure_bonus = 0.05 if content_length > 100 else 0.0
        
        confidence = base_confidence * length_factor + structure_bonus
        
        return min(1.0, max(0.0, confidence))
    
    def _get_capabilities(self) -> list:
        """Get Claude service capabilities."""
        
        return [
            "text_generation",
            "conversation",
            "analysis",
            "creative_writing",
            "reasoning",
            "summarization",
            "translation",
            "code_analysis"
        ]
    
    async def generate_quote(
        self,
        prompt: str,
        style: Optional[str] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """Generate a quote using Claude."""
        
        from .base import format_prompt_for_quotes
        
        formatted_prompt = format_prompt_for_quotes(
            base_prompt=prompt,
            style=style,
            tone=tone,
            length=length,
            context=context
        )
        
        request = AIRequest(
            task_type=AITaskType.QUOTE_GENERATION,
            prompt=formatted_prompt,
            **kwargs
        )
        
        return await self.generate_text(request)
    
    async def analyze_text(
        self,
        text: str,
        analysis_type: str = "comprehensive",
        **kwargs
    ) -> AIResponse:
        """Analyze text using Claude."""
        
        from .base import format_prompt_for_analysis
        
        formatted_prompt = format_prompt_for_analysis(text, analysis_type)
        
        task_mapping = {
            "sentiment": AITaskType.SENTIMENT_ANALYSIS,
            "psychology": AITaskType.PSYCHOLOGY_ANALYSIS,
            "comprehensive": AITaskType.TEXT_ANALYSIS,
            "themes": AITaskType.TEXT_ANALYSIS,
            "style": AITaskType.TEXT_ANALYSIS
        }
        
        task_type = task_mapping.get(analysis_type, AITaskType.TEXT_ANALYSIS)
        
        request = AIRequest(
            task_type=task_type,
            prompt=formatted_prompt,
            **kwargs
        )
        
        return await self.generate_text(request)