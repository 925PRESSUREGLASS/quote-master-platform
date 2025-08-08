"""
OpenAI Codex service implementation for Quote Master Pro.

This module provides integration with OpenAI's Codex models for code generation,
analysis, and programming assistance within the multi-agent AI system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

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


class CodexTaskType(str):
    """Codex-specific task types."""

    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_EXPLANATION = "code_explanation"
    CODE_REVIEW = "code_review"
    CODE_REFACTORING = "code_refactoring"
    CODE_DEBUGGING = "code_debugging"
    CODE_DOCUMENTATION = "code_documentation"
    UNIT_TEST_GENERATION = "unit_test_generation"
    API_INTEGRATION = "api_integration"
    DATABASE_QUERIES = "database_queries"


class CodexService(AIServiceBase):
    """OpenAI Codex service implementation for code generation and analysis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 45,  # Code generation may take longer
    ):
        self.timeout = timeout
        api_key = api_key or settings.openai_api_key
        model_name = model_name or "code-davinci-002"  # Default Codex model

        super().__init__(api_key=api_key, model_name=model_name)

        # Code generation specific settings
        self.supported_languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "csharp",
            "cpp",
            "c",
            "go",
            "rust",
            "php",
            "ruby",
            "swift",
            "kotlin",
            "scala",
            "r",
            "sql",
            "html",
            "css",
            "bash",
            "powershell",
            "yaml",
            "json",
            "xml",
        ]

        # Template mappings for different code tasks
        self.code_templates = {
            CodexTaskType.CODE_GENERATION: (
                "Generate {language} code for the following requirement:\n"
                "{requirement}\n\n"
                "Additional context: {context}\n"
                "Code style preferences: {style_preferences}\n\n"
                "Please provide clean, well-commented, production-ready code:"
            ),
            CodexTaskType.CODE_REVIEW: (
                "Review the following {language} code and provide feedback:\n\n"
                "```{language}\n{code}\n```\n\n"
                "Focus on:\n"
                "- Code quality and best practices\n"
                "- Performance optimizations\n"
                "- Security considerations\n"
                "- Maintainability and readability\n"
                "- Bug detection\n\n"
                "Provide detailed analysis with suggestions:"
            ),
            CodexTaskType.CODE_EXPLANATION: (
                "Explain the following {language} code in detail:\n\n"
                "```{language}\n{code}\n```\n\n"
                "Please provide:\n"
                "- Line-by-line explanation\n"
                "- Overall purpose and functionality\n"
                "- Key algorithms or patterns used\n"
                "- Input/output behavior\n"
                "- Dependencies and requirements:"
            ),
            CodexTaskType.UNIT_TEST_GENERATION: (
                "Generate comprehensive unit tests for this {language} code:\n\n"
                "```{language}\n{code}\n```\n\n"
                "Requirements:\n"
                "- Test framework: {test_framework}\n"
                "- Cover edge cases and error conditions\n"
                "- Include setup and teardown if needed\n"
                "- Use descriptive test names\n"
                "- Add comments explaining test scenarios:"
            ),
        }

    def _initialize_client(self) -> None:
        """Initialize OpenAI client for Codex."""
        try:
            openai.api_key = self.api_key
            self._client = openai
            logger.info(f"Codex client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Codex client: {str(e)}")
            raise AIServiceError(f"Failed to initialize Codex: {str(e)}", "Codex")

    async def _make_request(self, request: AIRequest) -> AIResponse:
        """Make a request to OpenAI Codex API."""

        try:
            # For Codex, we use the Completion API instead of Chat API
            full_prompt = self._build_code_prompt(request)

            # Prepare request parameters for code generation
            request_params = {
                "model": self.model_name,
                "prompt": full_prompt,
                "max_tokens": request.max_tokens or 1024,  # More tokens for code
                "temperature": request.temperature or 0.1,  # Lower temperature for code
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": ["```", "---", "###"],  # Common code block terminators
            }

            # Add additional parameters from request
            if request.parameters:
                request_params.update(self._filter_codex_params(request.parameters))

            # Make the API call with timeout
            response = await asyncio.wait_for(
                self._client.Completion.acreate(**request_params), timeout=self.timeout
            )

            # Extract the generated content
            content = response.choices[0].text.strip()

            # Post-process code content
            content = self._post_process_code(content, request)

            # Extract usage information
            usage_info = self._extract_usage_info(response)

            # Calculate confidence score
            confidence = self._calculate_code_confidence_score(
                response, request, content
            )

            # Build metadata
            metadata = {
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "response_id": response.id,
                "created": response.created,
                "language_detected": self._detect_language(content),
                "code_quality_score": self._assess_code_quality(content),
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
                f"Codex request timed out after {self.timeout} seconds", "Codex"
            )
        except openai.error.RateLimitError as e:
            raise AIServiceError(
                f"Codex rate limit exceeded: {str(e)}", "Codex", "RATE_LIMIT"
            )
        except Exception as e:
            logger.error(f"Unexpected Codex error: {str(e)}")
            raise AIServiceError(
                f"Unexpected Codex error: {str(e)}", "Codex", "UNKNOWN_ERROR"
            )

    def _build_code_prompt(self, request: AIRequest) -> str:
        """Build a specialized prompt for code generation tasks."""

        # Get task-specific template
        task_type = getattr(request, "code_task_type", CodexTaskType.CODE_GENERATION)
        template = self.code_templates.get(task_type)

        if template:
            # Extract parameters from request context
            language = request.parameters.get("language", "python")
            context = request.parameters.get("context", "")
            code = request.parameters.get("code", "")
            style_preferences = request.parameters.get(
                "style_preferences", "PEP 8 compliant"
            )
            test_framework = request.parameters.get("test_framework", "pytest")

            # Format the template
            try:
                formatted_prompt = template.format(
                    language=language,
                    requirement=request.prompt,
                    context=context,
                    code=code,
                    style_preferences=style_preferences,
                    test_framework=test_framework,
                )
            except KeyError:
                # Fallback if template formatting fails
                formatted_prompt = f"{template}\n\n{request.prompt}"
        else:
            # Default prompt for code tasks
            formatted_prompt = (
                f"Generate high-quality code for the following request:\n\n"
                f"{request.prompt}\n\n"
                f"Please provide clean, well-documented code with appropriate error handling:"
            )

        return formatted_prompt

    def _post_process_code(self, content: str, request: AIRequest) -> str:
        """Post-process generated code content."""

        # Remove common artifacts from code generation
        content = content.strip()

        # Remove any leading/trailing markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            if len(lines) > 1:
                content = "\n".join(lines[1:])
            if content.endswith("```"):
                content = content[:-3].strip()

        # Remove trailing explanatory text that's not code
        lines = content.split("\n")
        code_lines = []
        in_explanation = False

        for line in lines:
            # Skip lines that look like explanations after code
            if any(
                line.lower().startswith(phrase)
                for phrase in [
                    "this code",
                    "the above",
                    "explanation:",
                    "note:",
                    "here's how",
                    "this function",
                    "this script",
                ]
            ):
                in_explanation = True
                continue

            if not in_explanation or line.strip().startswith(
                ("#", "//", "/*", "*", "--")
            ):
                code_lines.append(line)

        return "\n".join(code_lines).strip()

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""

        # Simple language detection based on common patterns
        code_lower = code.lower()

        if "def " in code_lower and "import " in code_lower:
            return "python"
        elif "function " in code_lower and (
            "var " in code_lower or "let " in code_lower
        ):
            return "javascript"
        elif "class " in code_lower and "public " in code_lower:
            if "static void main" in code_lower:
                return "java"
            elif "namespace " in code_lower:
                return "csharp"
        elif "#include" in code_lower:
            return "cpp" if "std::" in code_lower else "c"
        elif "package " in code_lower and "func " in code_lower:
            return "go"
        elif "fn " in code_lower and "let " in code_lower:
            return "rust"
        elif "SELECT " in code.upper() and "FROM " in code.upper():
            return "sql"
        elif "<html" in code_lower or "<!DOCTYPE" in code_lower:
            return "html"
        elif (
            "{" in code
            and "}" in code
            and ("color:" in code_lower or "margin:" in code_lower)
        ):
            return "css"
        elif "#!/bin/bash" in code or "echo " in code_lower:
            return "bash"

        return "unknown"

    def _assess_code_quality(self, code: str) -> float:
        """Assess basic code quality metrics."""

        if not code or len(code) < 10:
            return 0.0

        quality_score = 0.5  # Base score

        # Check for comments
        comment_ratio = self._calculate_comment_ratio(code)
        quality_score += min(0.2, comment_ratio * 0.4)

        # Check for proper structure (functions, classes)
        if any(keyword in code.lower() for keyword in ["def ", "function ", "class "]):
            quality_score += 0.1

        # Check for error handling
        if any(
            keyword in code.lower() for keyword in ["try", "catch", "except", "error"]
        ):
            quality_score += 0.1

        # Penalize overly long lines
        lines = code.split("\n")
        long_line_ratio = sum(1 for line in lines if len(line) > 120) / max(
            len(lines), 1
        )
        quality_score -= min(0.1, long_line_ratio * 0.2)

        return min(1.0, max(0.0, quality_score))

    def _calculate_comment_ratio(self, code: str) -> float:
        """Calculate the ratio of comment lines to total lines."""

        lines = code.split("\n")
        if not lines:
            return 0.0

        comment_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("#", "//", "/*", "*", "--", "<!--")):
                comment_lines += 1

        return comment_lines / len(lines)

    def _filter_codex_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter and validate parameters for Codex API."""

        valid_params = {
            "temperature",
            "top_p",
            "max_tokens",
            "presence_penalty",
            "frequency_penalty",
            "logit_bias",
            "user",
            "stop",
            "suffix",
        }

        return {k: v for k, v in params.items() if k in valid_params}

    def _calculate_code_confidence_score(
        self, response: Any, request: AIRequest, content: str
    ) -> float:
        """Calculate confidence score for Codex response."""

        finish_reason = response.choices[0].finish_reason

        # Base confidence based on finish reason
        if finish_reason == "stop":
            base_confidence = 0.9
        elif finish_reason == "length":
            base_confidence = 0.7
        else:
            base_confidence = 0.5

        # Adjust based on code quality assessment
        quality_score = self._assess_code_quality(content)
        quality_factor = 0.8 + (quality_score * 0.2)

        # Adjust based on language detection
        detected_lang = self._detect_language(content)
        lang_factor = 1.0 if detected_lang != "unknown" else 0.8

        # Final confidence score
        confidence = base_confidence * quality_factor * lang_factor

        return min(1.0, max(0.0, confidence))

    def _extract_usage_info(self, response: Any) -> Dict[str, Any]:
        """Extract usage information from Codex response."""

        usage = response.get("usage", {})

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Codex pricing (simplified - update with current pricing)
        cost_per_1k_tokens = 0.002  # Codex cost estimate
        estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": round(estimated_cost, 6),
        }

    def _get_capabilities(self) -> List[str]:
        """Get Codex service capabilities."""

        return [
            "code_generation",
            "code_completion",
            "code_explanation",
            "code_review",
            "code_refactoring",
            "bug_detection",
            "unit_test_generation",
            "code_documentation",
            "api_integration",
            "database_queries",
            "algorithm_implementation",
            "code_optimization",
        ]

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Codex model."""

        return {
            "provider": "OpenAI",
            "model": self.model_name,
            "type": "Code Generation Model",
            "capabilities": self._get_capabilities(),
            "max_tokens": 8192,
            "supported_languages": self.supported_languages,
            "supports_chat": False,
            "supports_streaming": True,
            "specialization": "code_generation",
        }

    async def generate_code(
        self,
        requirement: str,
        language: str = "python",
        context: Optional[str] = None,
        style_preferences: str = "best_practices",
        **kwargs,
    ) -> AIResponse:
        """Generate code for a specific requirement."""

        request = AIRequest(
            task_type=AITaskType.QUOTE_GENERATION,  # Using base type
            prompt=requirement,
            parameters={
                "language": language,
                "context": context or "",
                "style_preferences": style_preferences,
                "code_task_type": CodexTaskType.CODE_GENERATION,
            },
            **kwargs,
        )

        # Set code task type as attribute
        request.code_task_type = CodexTaskType.CODE_GENERATION

        return await self.generate_text(request)

    async def review_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: Optional[List[str]] = None,
        **kwargs,
    ) -> AIResponse:
        """Review code and provide feedback."""

        request = AIRequest(
            task_type=AITaskType.TEXT_ANALYSIS,
            prompt=f"Review this {language} code",
            parameters={
                "language": language,
                "code": code,
                "focus_areas": focus_areas or ["quality", "performance", "security"],
                "code_task_type": CodexTaskType.CODE_REVIEW,
            },
            **kwargs,
        )

        request.code_task_type = CodexTaskType.CODE_REVIEW

        return await self.generate_text(request)

    async def explain_code(
        self,
        code: str,
        language: str = "python",
        detail_level: str = "comprehensive",
        **kwargs,
    ) -> AIResponse:
        """Explain code functionality and structure."""

        request = AIRequest(
            task_type=AITaskType.TEXT_ANALYSIS,
            prompt=f"Explain this {language} code",
            parameters={
                "language": language,
                "code": code,
                "detail_level": detail_level,
                "code_task_type": CodexTaskType.CODE_EXPLANATION,
            },
            **kwargs,
        )

        request.code_task_type = CodexTaskType.CODE_EXPLANATION

        return await self.generate_text(request)

    async def generate_tests(
        self,
        code: str,
        language: str = "python",
        test_framework: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate unit tests for given code."""

        # Default test frameworks by language
        default_frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "java": "junit",
            "csharp": "nunit",
            "go": "testing",
            "rust": "cargo_test",
        }

        framework = test_framework or default_frameworks.get(language, "unit_test")

        request = AIRequest(
            task_type=AITaskType.QUOTE_GENERATION,
            prompt=f"Generate comprehensive unit tests",
            parameters={
                "language": language,
                "code": code,
                "test_framework": framework,
                "code_task_type": CodexTaskType.UNIT_TEST_GENERATION,
            },
            **kwargs,
        )

        request.code_task_type = CodexTaskType.UNIT_TEST_GENERATION

        return await self.generate_text(request)

    async def health_check(self) -> bool:
        """Perform health check on Codex service."""

        try:
            # Simple health check with minimal code generation
            test_request = AIRequest(
                task_type=AITaskType.QUOTE_GENERATION,
                prompt="def hello_world():",
                max_tokens=50,
            )

            response = await self.generate_text(test_request)
            return response.success and len(response.content) > 0

        except Exception as e:
            logger.error("Codex health check failed: %s", e)
            return False
