"""OpenAI service implementation for Quote Master Pro."""

import asyncio
import logging
from typing import Any, Dict, Optional

import openai

from src.core.config import get_settings

from .base import (
    AIRequest,
    AIResponse,
    AIServiceBase,
    AIServiceError,
    AIServiceTimeoutError,
    AITaskType,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIService(AIServiceBase):
    """OpenAI service implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 30,
    ):
        self.timeout = timeout
        api_key = api_key or settings.openai_api_key
        model_name = model_name or settings.openai_model

        super().__init__(api_key=api_key, model_name=model_name)

    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            openai.api_key = self.api_key
            self._client = openai
            logger.info(f"OpenAI client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise AIServiceError(f"Failed to initialize OpenAI: {str(e)}", "OpenAI")

    async def _make_request(self, request: AIRequest) -> AIResponse:
        """Make a request to OpenAI API."""

        try:
            # Build the complete prompt
            full_prompt = self._build_prompt(request)

            # Prepare request parameters
            request_params = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_message(request.task_type),
                    },
                    {"role": "user", "content": full_prompt},
                ],
                "max_tokens": request.max_tokens or settings.openai_max_tokens,
                "temperature": request.temperature or settings.openai_temperature,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
            }

            # Add additional parameters from request
            if request.parameters:
                request_params.update(self._filter_openai_params(request.parameters))

            # Make the API call with timeout
            response = await asyncio.wait_for(
                self._client.ChatCompletion.acreate(**request_params),
                timeout=self.timeout,
            )

            # Extract the generated content
            content = response.choices[0].message.content.strip()

            # Extract usage information
            usage_info = self._extract_usage_info(response)

            # Calculate confidence score
            confidence = self._calculate_confidence_score(response, request)

            # Build metadata
            metadata = {
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id,
                "created": response.created,
            }

            return AIResponse(
                success=True,
                content=content,
                model_used=self.model_name,
                task_type=request.task_type,
                metadata=metadata,
                usage=usage_info,
                processing_time=0.0,  # Will be set by parent class
                confidence_score=confidence,
            )

        except asyncio.TimeoutError:
            raise AIServiceTimeoutError(
                f"OpenAI request timed out after {self.timeout} seconds", "OpenAI"
            )
        except openai.error.RateLimitError as e:
            raise AIServiceError(
                f"OpenAI rate limit exceeded: {str(e)}", "OpenAI", "RATE_LIMIT"
            )
        except openai.error.InvalidRequestError as e:
            raise AIServiceError(
                f"Invalid OpenAI request: {str(e)}", "OpenAI", "INVALID_REQUEST"
            )
        except openai.error.AuthenticationError as e:
            raise AIServiceError(
                f"OpenAI authentication failed: {str(e)}", "OpenAI", "AUTH_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {str(e)}")
            raise AIServiceError(
                f"Unexpected OpenAI error: {str(e)}", "OpenAI", "UNKNOWN_ERROR"
            )

    def _get_system_message(self, task_type: AITaskType) -> str:
        """Get system message for different task types, optimized for different model tiers."""

        # Enhanced system messages optimized for model capabilities
        if "gpt-5" in self.model_name.lower() or "o3-pro" in self.model_name.lower():
            # Enhanced prompts for flagship models with reasoning capabilities
            system_messages = {
                AITaskType.QUOTE_GENERATION: (
                    "You are Quote Master Pro, an advanced AI with deep reasoning capabilities. "
                    "Create original, profound quotes that demonstrate wisdom, philosophical insight, "
                    "and emotional intelligence. Consider multiple perspectives, cultural contexts, "
                    "and the deeper psychological impact of your words. Each quote should be "
                    "memorable, transformative, and provide genuine value to diverse audiences."
                ),
                AITaskType.PSYCHOLOGY_ANALYSIS: (
                    "You are an expert psychologist with advanced analytical reasoning. Perform "
                    "comprehensive psychological analysis considering cognitive patterns, emotional "
                    "dynamics, behavioral indicators, and developmental frameworks. Provide deep "
                    "insights into personality structures, defense mechanisms, and growth opportunities."
                ),
            }
        else:
            # Standard system messages for regular models
            system_messages = {
                AITaskType.QUOTE_GENERATION: (
                    "You are Quote Master Pro, an expert quote generator. Your mission is to create "
                    "original, inspiring, and meaningful quotes that resonate deeply with people. "
                    "Focus on wisdom, clarity, and emotional impact. Each quote should be memorable, "
                    "shareable, and provide genuine value to the reader."
                ),
                AITaskType.PSYCHOLOGY_ANALYSIS: (
                    "You are a psychology expert specializing in text analysis. Identify psychological "
                    "patterns, emotional intelligence insights, cognitive frameworks, and personal "
                    "development opportunities in the given text."
                ),
            }

        # Common system messages for all models
        system_messages.update(
            {
                AITaskType.TEXT_ANALYSIS: (
                    "You are an expert text analyst. Provide comprehensive, insightful analysis "
                    "of text including themes, sentiment, style, and deeper meanings. Be thorough "
                    "and objective in your observations."
                ),
                AITaskType.SENTIMENT_ANALYSIS: (
                    "You are a sentiment analysis expert. Analyze text for emotional content, "
                    "tone, and sentiment. Provide accurate sentiment scores and detailed reasoning."
                ),
                AITaskType.CONTENT_MODERATION: (
                    "You are a content moderation specialist. Evaluate content for appropriateness, "
                    "safety, and compliance with community guidelines. Consider context and intent."
                ),
            }
        )

        default_message = (
            "You are a helpful AI assistant specialized in text generation and analysis. "
            "Provide thoughtful, accurate, and well-reasoned responses."
        )

        # Enhanced default for flagship models
        if "gpt-5" in self.model_name.lower() or "o3-pro" in self.model_name.lower():
            default_message = (
                "You are an advanced AI assistant with sophisticated reasoning capabilities. "
                "Provide comprehensive, nuanced, and deeply insightful responses that demonstrate "
                "critical thinking and multi-dimensional analysis."
            )

        return system_messages.get(task_type, default_message)

    def _filter_openai_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and validate parameters for OpenAI API."""

        # List of valid OpenAI ChatCompletion parameters (updated for 2025 models)
        valid_params = {
            "temperature",
            "top_p",
            "max_tokens",
            "presence_penalty",
            "frequency_penalty",
            "logit_bias",
            "user",
            "stop",
            "seed",
            "response_format",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
        }

        return {k: v for k, v in params.items() if k in valid_params}

    def _extract_usage_info(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from OpenAI response."""

        usage = response.get("usage", {})

        # Calculate cost estimate (simplified pricing)
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Updated pricing estimates for 2024/2025 models
        if "gpt-5" in self.model_name.lower():
            # GPT-5 (Estimated pricing when available)
            cost_per_1k_prompt = 0.05
            cost_per_1k_completion = 0.10
        elif "o3-pro" in self.model_name.lower() or "o3pro" in self.model_name.lower():
            # o3-pro (Estimated reasoning model pricing)
            cost_per_1k_prompt = 0.20
            cost_per_1k_completion = 0.40
        elif "gpt-4o" in self.model_name.lower():
            if "mini" in self.model_name.lower():
                # GPT-4o mini
                cost_per_1k_prompt = 0.000150
                cost_per_1k_completion = 0.000600
            else:
                # GPT-4o (standard)
                cost_per_1k_prompt = 0.0025
                cost_per_1k_completion = 0.01
        elif "gpt-4" in self.model_name.lower():
            if "turbo" in self.model_name.lower():
                # GPT-4 Turbo
                cost_per_1k_prompt = 0.01
                cost_per_1k_completion = 0.03
            else:
                # GPT-4 (legacy)
                cost_per_1k_prompt = 0.03
                cost_per_1k_completion = 0.06
        else:  # GPT-3.5
            cost_per_1k_prompt = 0.0015
            cost_per_1k_completion = 0.002

        estimated_cost = (prompt_tokens / 1000) * cost_per_1k_prompt + (
            completion_tokens / 1000
        ) * cost_per_1k_completion

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": round(estimated_cost, 6),
        }

    def _calculate_confidence_score(self, response: Any, request: AIRequest) -> float:
        """Calculate confidence score for OpenAI response, considering model capabilities."""

        choice = response.choices[0]
        finish_reason = choice.finish_reason
        content_length = len(choice.message.content)

        # Base confidence based on finish reason
        if finish_reason == "stop":
            base_confidence = 0.9
        elif finish_reason == "length":
            base_confidence = 0.7  # Truncated due to length
        else:
            base_confidence = 0.5

        # Adjust base confidence for model tier
        if "gpt-5" in self.model_name.lower():
            base_confidence = min(1.0, base_confidence + 0.05)  # GPT-5 bonus
        elif "o3-pro" in self.model_name.lower():
            base_confidence = min(1.0, base_confidence + 0.08)  # o3-pro reasoning bonus
        elif (
            "gpt-4o" in self.model_name.lower()
            and "mini" not in self.model_name.lower()
        ):
            base_confidence = min(1.0, base_confidence + 0.03)  # GPT-4o bonus

        # Adjust based on content length vs expected length
        expected_length = request.max_tokens * 0.7  # Rough estimate
        if content_length >= expected_length * 0.8:
            length_factor = 1.0
        elif content_length >= expected_length * 0.5:
            length_factor = 0.9
        else:
            length_factor = 0.8

        # Final confidence score
        confidence = base_confidence * length_factor

        return min(1.0, max(0.0, confidence))

    def _get_capabilities(self) -> list:
        """Get OpenAI service capabilities based on model tier."""

        base_capabilities = [
            "text_generation",
            "conversation",
            "question_answering",
            "creative_writing",
            "code_generation",
            "translation",
            "summarization",
            "analysis",
        ]

        # Enhanced capabilities for advanced models
        if "gpt-5" in self.model_name.lower():
            base_capabilities.extend(
                [
                    "advanced_reasoning",
                    "multi_modal_analysis",
                    "complex_problem_solving",
                    "philosophical_analysis",
                    "scientific_research",
                ]
            )
        elif "o3-pro" in self.model_name.lower():
            base_capabilities.extend(
                [
                    "step_by_step_reasoning",
                    "mathematical_proofs",
                    "logical_deduction",
                    "complex_analysis",
                    "research_methodology",
                ]
            )
        elif "gpt-4" in self.model_name.lower():
            base_capabilities.extend(
                ["function_calling", "structured_output", "advanced_analysis"]
            )

        return base_capabilities

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current OpenAI model with updated model specs."""

        # Model-specific information
        if "gpt-5" in self.model_name.lower():
            max_tokens = 200000  # Estimated for GPT-5
            context_window = 1000000  # Estimated context window
            model_type = "Advanced Language Model"
        elif "o3-pro" in self.model_name.lower():
            max_tokens = 100000  # Estimated for o3-pro
            context_window = 500000  # Estimated context window
            model_type = "Reasoning Model"
        elif "gpt-4o" in self.model_name.lower():
            max_tokens = 128000
            context_window = 128000
            model_type = "Multimodal Language Model"
        elif "gpt-4" in self.model_name.lower():
            max_tokens = 8192 if "turbo" in self.model_name.lower() else 4096
            context_window = 128000 if "turbo" in self.model_name.lower() else 8192
            model_type = "Language Model"
        else:
            max_tokens = 4096
            context_window = 16384
            model_type = "Language Model"

        return {
            "provider": "OpenAI",
            "model": self.model_name,
            "type": model_type,
            "capabilities": self._get_capabilities(),
            "max_tokens": max_tokens,
            "context_window": context_window,
            "supports_chat": True,
            "supports_streaming": True,
            "supports_tools": "gpt-4" in self.model_name.lower()
            or "gpt-5" in self.model_name.lower(),
            "supports_reasoning": "o3" in self.model_name.lower(),
        }

    async def generate_quote(
        self,
        prompt: str,
        style: Optional[str] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate a quote using OpenAI."""

        from .base import format_prompt_for_quotes

        formatted_prompt = format_prompt_for_quotes(
            base_prompt=prompt, style=style, tone=tone, length=length, context=context
        )

        request = AIRequest(
            task_type=AITaskType.QUOTE_GENERATION, prompt=formatted_prompt, **kwargs
        )

        return await self.generate_text(request)

    async def analyze_text(
        self, text: str, analysis_type: str = "comprehensive", **kwargs
    ) -> AIResponse:
        """Analyze text using OpenAI."""

        from .base import format_prompt_for_analysis

        formatted_prompt = format_prompt_for_analysis(text, analysis_type)

        task_mapping = {
            "sentiment": AITaskType.SENTIMENT_ANALYSIS,
            "psychology": AITaskType.PSYCHOLOGY_ANALYSIS,
            "comprehensive": AITaskType.TEXT_ANALYSIS,
            "themes": AITaskType.TEXT_ANALYSIS,
            "style": AITaskType.TEXT_ANALYSIS,
        }

        task_type = task_mapping.get(analysis_type, AITaskType.TEXT_ANALYSIS)

        request = AIRequest(task_type=task_type, prompt=formatted_prompt, **kwargs)

        return await self.generate_text(request)

    async def moderate_content(self, content: str) -> Dict[str, Any]:
        """Use OpenAI's moderation API to check content."""

        try:
            response = await self._client.Moderation.acreate(input=content)

            moderation_result = response.results[0]

            return {
                "flagged": moderation_result.flagged,
                "categories": dict(moderation_result.categories),
                "category_scores": dict(moderation_result.category_scores),
            }

        except Exception as e:
            logger.error(f"OpenAI content moderation failed: {str(e)}")
            return {
                "flagged": False,
                "categories": {},
                "category_scores": {},
                "error": str(e),
            }
