"""
Token Optimization System for Multi-Agent AI Orchestration

This module provides intelligent token usage optimization across different AI providers,
implementing cost-efficient routing and request optimization strategies.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .agent_types import (
    PROVIDER_MODEL_MAPPING,
    AgentRole,
    ProviderTier,
    TaskComplexity,
    get_optimal_provider,
)


class TokenStrategy(str, Enum):
    """Token optimization strategies."""

    COST_MINIMIZED = "cost_minimized"  # Minimize cost above all
    BALANCED = "balanced"  # Balance cost vs quality
    QUALITY_FIRST = "quality_first"  # Quality first, cost secondary
    SPEED_OPTIMIZED = "speed_optimized"  # Optimize for response time
    CUSTOM = "custom"  # Custom optimization rules


class OptimizationMetric(str, Enum):
    """Metrics for optimization decisions."""

    COST_PER_TOKEN = "cost_per_token"
    RESPONSE_TIME = "response_time"
    QUALITY_SCORE = "quality_score"
    SUCCESS_RATE = "success_rate"
    TOKEN_EFFICIENCY = "token_efficiency"


@dataclass
class TokenUsageStats:
    """Token usage statistics for optimization decisions."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    response_time_ms: float = 0.0
    quality_score: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ProviderPerformance:
    """Performance metrics for each provider."""

    provider: str
    model: str
    tier: ProviderTier

    # Cost metrics
    cost_per_1k_tokens: float
    avg_cost_per_request: float

    # Performance metrics
    avg_response_time_ms: float
    success_rate: float
    avg_quality_score: float

    # Usage stats
    total_requests: int = 0
    total_tokens: int = 0
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class TokenOptimizer:
    """Optimizes token usage and provider selection for cost efficiency."""

    def __init__(self):
        self.strategy = TokenStrategy.BALANCED
        self.performance_cache: Dict[str, ProviderPerformance] = {}
        self.usage_history: List[TokenUsageStats] = []
        self.optimization_rules: Dict[str, Any] = {}

        # Initialize with baseline provider data
        self._initialize_provider_baselines()

        # Cost thresholds (USD)
        self.cost_thresholds = {
            TaskComplexity.SIMPLE: 0.001,  # $0.001 per request
            TaskComplexity.MODERATE: 0.005,  # $0.005 per request
            TaskComplexity.COMPLEX: 0.02,  # $0.02 per request
            TaskComplexity.CRITICAL: 0.10,  # $0.10 per request (no limit)
        }

    def _initialize_provider_baselines(self):
        """Initialize baseline performance data for providers."""

        # Current market rates (as of late 2024)
        baseline_costs = {
            "gpt-4o-mini": 0.00015,  # $0.15 per 1M tokens
            "gpt-4o": 0.0025,  # $2.50 per 1M tokens
            "gpt-4-turbo": 0.01,  # $10 per 1M tokens
            "gpt-5": 0.05,  # Estimated $50 per 1M tokens
            "o3-pro": 0.20,  # Estimated $200 per 1M tokens (reasoning)
            "claude-3-haiku-20240307": 0.00025,  # $0.25 per 1M tokens
            "claude-3-sonnet-20240229": 0.003,  # $3 per 1M tokens
            "claude-3-opus-20240229": 0.015,  # $15 per 1M tokens
        }

        # Initialize performance baselines
        for tier, providers in PROVIDER_MODEL_MAPPING.items():
            for provider, model in providers.items():
                cost = baseline_costs.get(model, 0.001)  # Default fallback

                self.performance_cache[f"{provider}:{model}"] = ProviderPerformance(
                    provider=provider,
                    model=model,
                    tier=tier,
                    cost_per_1k_tokens=cost,
                    avg_cost_per_request=cost * 500,  # Assume 500 tokens average
                    avg_response_time_ms=2000,  # 2 second baseline
                    success_rate=0.98,  # 98% baseline success rate
                    avg_quality_score=0.8,  # 80% baseline quality
                )

    def set_strategy(
        self, strategy: TokenStrategy, custom_rules: Optional[Dict] = None
    ):
        """Set optimization strategy with optional custom rules."""

        self.strategy = strategy

        if strategy == TokenStrategy.CUSTOM and custom_rules:
            self.optimization_rules = custom_rules
        else:
            # Set default rules based on strategy
            self.optimization_rules = self._get_default_rules(strategy)

    def _get_default_rules(self, strategy: TokenStrategy) -> Dict[str, Any]:
        """Get default optimization rules for a strategy."""

        rules = {
            TokenStrategy.COST_MINIMIZED: {
                "cost_weight": 1.0,
                "quality_weight": 0.2,
                "speed_weight": 0.1,
                "max_cost_per_request": 0.01,
            },
            TokenStrategy.BALANCED: {
                "cost_weight": 0.4,
                "quality_weight": 0.4,
                "speed_weight": 0.2,
                "max_cost_per_request": 0.05,
            },
            TokenStrategy.QUALITY_FIRST: {
                "cost_weight": 0.1,
                "quality_weight": 0.8,
                "speed_weight": 0.1,
                "max_cost_per_request": 0.20,
            },
            TokenStrategy.SPEED_OPTIMIZED: {
                "cost_weight": 0.2,
                "quality_weight": 0.3,
                "speed_weight": 0.5,
                "max_cost_per_request": 0.10,
            },
        }

        return rules.get(strategy, rules[TokenStrategy.BALANCED])

    async def optimize_request(
        self,
        agent_role: AgentRole,
        prompt: str,
        context: Optional[str] = None,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """Optimize a request for minimal token usage while maintaining quality."""

        # Estimate token usage
        estimated_tokens = self._estimate_tokens(prompt, context, max_tokens)

        # Get optimal provider based on agent role and complexity
        optimal_tier = get_optimal_provider(agent_role, task_complexity)

        # Find best provider within budget
        provider_key = await self._select_optimal_provider(
            optimal_tier, estimated_tokens, task_complexity
        )

        # Optimize prompt for selected provider
        optimized_prompt = self._optimize_prompt(prompt, provider_key, estimated_tokens)

        # Calculate cost estimate
        provider_perf = self.performance_cache.get(provider_key)
        estimated_cost = (
            (estimated_tokens / 1000) * provider_perf.cost_per_1k_tokens
            if provider_perf
            else 0.01
        )

        return {
            "provider_key": provider_key,
            "optimized_prompt": optimized_prompt,
            "optimized_context": context,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": estimated_cost,
            "max_tokens": max_tokens,
            "optimization_metadata": {
                "original_prompt_length": len(prompt),
                "optimized_prompt_length": len(optimized_prompt),
                "compression_ratio": len(optimized_prompt) / len(prompt)
                if prompt
                else 1.0,
                "selected_tier": optimal_tier.value,
                "strategy": self.strategy.value,
            },
        }

    async def _select_optimal_provider(
        self,
        preferred_tier: ProviderTier,
        estimated_tokens: int,
        task_complexity: TaskComplexity,
    ) -> str:
        """Select the optimal provider based on current performance and costs."""

        # Get cost threshold for this task complexity
        max_cost = self.cost_thresholds.get(task_complexity, 0.05)

        # Filter providers by tier and cost
        candidates = []
        for key, perf in self.performance_cache.items():
            estimated_cost = (estimated_tokens / 1000) * perf.cost_per_1k_tokens

            # Check if within budget
            if estimated_cost <= max_cost:
                candidates.append((key, perf, estimated_cost))

        if not candidates:
            # Fallback to cheapest available if over budget
            candidates = [
                (k, p, (estimated_tokens / 1000) * p.cost_per_1k_tokens)
                for k, p in self.performance_cache.items()
            ]
            candidates.sort(key=lambda x: x[2])  # Sort by cost

        # Score candidates based on strategy
        best_candidate = self._score_candidates(candidates)

        return best_candidate[0] if best_candidate else "openai:gpt-4o-mini"

    def _score_candidates(
        self, candidates: List[Tuple[str, ProviderPerformance, float]]
    ) -> Optional[Tuple[str, ProviderPerformance, float]]:
        """Score provider candidates based on current strategy."""

        if not candidates:
            return None

        rules = self.optimization_rules
        cost_weight = rules.get("cost_weight", 0.4)
        quality_weight = rules.get("quality_weight", 0.4)
        speed_weight = rules.get("speed_weight", 0.2)

        scored_candidates = []

        for provider_key, perf, estimated_cost in candidates:
            # Normalize metrics (0-1 scale, higher is better)
            cost_score = 1 / (estimated_cost + 0.001)  # Inverse cost
            quality_score = perf.avg_quality_score
            speed_score = 1 / (perf.avg_response_time_ms / 1000 + 0.1)  # Inverse time
            success_score = perf.success_rate

            # Calculate weighted score
            final_score = (
                cost_score * cost_weight
                + quality_score * quality_weight
                + speed_score * speed_weight
                + success_score * 0.1  # Small success rate bonus
            )

            scored_candidates.append((provider_key, perf, estimated_cost, final_score))

        # Return highest scoring candidate
        return max(scored_candidates, key=lambda x: x[3])

    def _estimate_tokens(
        self, prompt: str, context: Optional[str] = None, max_tokens: int = 500
    ) -> int:
        """Estimate token usage for a request."""

        # Rough estimation: ~4 characters per token for English text
        prompt_chars = len(prompt)
        context_chars = len(context) if context else 0

        # Input tokens
        input_tokens = (prompt_chars + context_chars) // 4

        # Output tokens (use max_tokens as estimate)
        output_tokens = max_tokens

        # Add some overhead for system messages, formatting, etc.
        overhead_tokens = 50

        return input_tokens + output_tokens + overhead_tokens

    def _optimize_prompt(
        self, prompt: str, provider_key: str, estimated_tokens: int
    ) -> str:
        """Optimize prompt for token efficiency while maintaining effectiveness."""

        # For simple tasks with economy providers, compress prompts
        if "mini" in provider_key.lower() or estimated_tokens > 1000:
            return self._compress_prompt(prompt)

        # For premium providers, keep full prompt for quality
        return prompt

    def _compress_prompt(self, prompt: str) -> str:
        """Compress prompt to reduce token usage."""

        # Remove redundant whitespace
        compressed = " ".join(prompt.split())

        # Remove common filler words for AI tasks
        filler_words = [
            "please",
            "kindly",
            "could you",
            "would you",
            "I need",
            "I want",
            "I would like",
            "it would be great if",
            "if possible",
        ]

        for filler in filler_words:
            compressed = compressed.replace(filler, "")

        # Clean up extra spaces
        compressed = " ".join(compressed.split())

        return compressed.strip()

    async def record_usage(self, provider_key: str, usage_stats: TokenUsageStats):
        """Record actual usage for performance tracking and optimization."""

        # Update provider performance metrics
        if provider_key in self.performance_cache:
            perf = self.performance_cache[provider_key]

            # Update moving averages
            alpha = 0.1  # Learning rate for exponential moving average

            perf.avg_response_time_ms = (
                1 - alpha
            ) * perf.avg_response_time_ms + alpha * usage_stats.response_time_ms

            perf.avg_quality_score = (
                1 - alpha
            ) * perf.avg_quality_score + alpha * usage_stats.quality_score

            perf.avg_cost_per_request = (
                1 - alpha
            ) * perf.avg_cost_per_request + alpha * usage_stats.cost_usd

            # Update counters
            perf.total_requests += 1
            perf.total_tokens += usage_stats.total_tokens
            perf.last_updated = datetime.now()

        # Store in usage history
        self.usage_history.append(usage_stats)

        # Keep only recent history (last 1000 entries)
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]

    def get_cost_analysis(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get cost analysis for the specified time window."""

        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_usage = [
            usage for usage in self.usage_history if usage.timestamp >= cutoff_time
        ]

        if not recent_usage:
            return {"error": "No usage data in specified time window"}

        total_cost = sum(usage.cost_usd for usage in recent_usage)
        total_tokens = sum(usage.total_tokens for usage in recent_usage)
        avg_cost_per_1k_tokens = (
            (total_cost / total_tokens * 1000) if total_tokens > 0 else 0
        )

        # Provider breakdown
        provider_costs = {}
        for usage in recent_usage:
            # You'd need to track provider in usage_stats for this to work
            provider = getattr(usage, "provider_key", "unknown")
            if provider not in provider_costs:
                provider_costs[provider] = {"cost": 0, "tokens": 0, "requests": 0}

            provider_costs[provider]["cost"] += usage.cost_usd
            provider_costs[provider]["tokens"] += usage.total_tokens
            provider_costs[provider]["requests"] += 1

        return {
            "time_window_hours": time_window_hours,
            "total_requests": len(recent_usage),
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "avg_cost_per_request": total_cost / len(recent_usage),
            "avg_cost_per_1k_tokens": avg_cost_per_1k_tokens,
            "provider_breakdown": provider_costs,
            "optimization_strategy": self.strategy.value,
        }

    def get_recommendations(self) -> List[str]:
        """Get optimization recommendations based on usage patterns."""

        recommendations = []

        if len(self.usage_history) < 10:
            recommendations.append("Insufficient usage data for recommendations")
            return recommendations

        # Analyze recent usage
        recent_usage = self.usage_history[-100:]  # Last 100 requests
        avg_cost = sum(u.cost_usd for u in recent_usage) / len(recent_usage)
        avg_quality = sum(u.quality_score for u in recent_usage) / len(recent_usage)

        # Cost-based recommendations
        if avg_cost > 0.05:
            recommendations.append(
                "Consider using more economy-tier models for simple tasks to reduce costs"
            )

        # Quality-based recommendations
        if avg_quality < 0.7:
            recommendations.append(
                "Consider using higher-tier models to improve output quality"
            )

        # Token efficiency recommendations
        avg_tokens = sum(u.total_tokens for u in recent_usage) / len(recent_usage)
        if avg_tokens > 800:
            recommendations.append("Enable prompt compression to reduce token usage")

        return recommendations
