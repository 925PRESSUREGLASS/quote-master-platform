"""
Enhanced AI Orchestrator with Multi-Agent Support and Token Optimization

This module extends the existing orchestrator with specialized agent capabilities,
intelligent token usage, and support for future models like GPT-5 and o3-pro.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..enhanced_ai_service import AIRequest as BaseAIRequest
from ..enhanced_ai_service import AIResponse, EnhancedAIService, get_ai_service
from ..orchestrator import AIOrchestrator
from ..orchestrator import RoutingStrategy as BaseRoutingStrategy
from .agent_types import (
    AGENT_CAPABILITIES,
    PROVIDER_MODEL_MAPPING,
    AgentCapability,
    AgentContext,
    AgentRole,
    ProviderTier,
    TaskComplexity,
    get_optimal_provider,
)
from .token_optimizer import TokenOptimizer, TokenStrategy, TokenUsageStats

logger = logging.getLogger(__name__)


class AgentRequest(BaseAIRequest):
    """Enhanced AI request with agent-specific context."""

    def __init__(
        self, prompt: str, agent_role: AgentRole, context: AgentContext, **kwargs
    ):
        super().__init__(prompt, **kwargs)
        self.agent_role = agent_role
        self.context = context
        self.request_id = str(uuid.uuid4())
        self.created_at = datetime.now()


class EnhancedAIOrchestrator:
    """
    Enhanced AI orchestrator with multi-agent support and intelligent token optimization.

    This orchestrator builds upon the existing infrastructure to provide:
    - Specialized agent roles for different tasks
    - Intelligent token usage optimization
    - Support for future models (GPT-5, o3-pro)
    - Advanced workflow coordination
    - Comprehensive monitoring and cost tracking
    """

    def __init__(self):
        self.base_orchestrator = None  # Will initialize from existing service
        self.enhanced_ai_service: Optional[EnhancedAIService] = None
        self.token_optimizer = TokenOptimizer()

        # Agent management
        self.active_agents: Dict[str, Dict] = {}
        self.agent_workflows: Dict[str, List] = {}

        # Performance tracking
        self.agent_metrics: Dict[AgentRole, Dict[str, Any]] = {}
        self.workflow_metrics: Dict[str, Dict[str, Any]] = {}

        # Configuration
        self.max_concurrent_agents = 5
        self.workflow_timeout_seconds = 300  # 5 minutes

        # Initialize agent metrics
        self._initialize_agent_metrics()

    async def initialize(self):
        """Initialize the enhanced orchestrator with existing services."""
        try:
            # Get the existing enhanced AI service
            self.enhanced_ai_service = await get_ai_service()

            # Set token optimization strategy
            self.token_optimizer.set_strategy(TokenStrategy.BALANCED)

            logger.info("Enhanced AI Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Enhanced AI Orchestrator: {e}")
            raise

    def _initialize_agent_metrics(self):
        """Initialize metrics tracking for all agent roles."""
        for role in AgentRole:
            self.agent_metrics[role] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time_ms": 0.0,
                "avg_cost_usd": 0.0,
                "avg_quality_score": 0.0,
                "avg_token_efficiency": 0.0,
                "last_used": None,
                "preferred_providers": [],
                "cost_savings_usd": 0.0,
            }

    async def execute_agent_task(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Execute a task using the specified agent with optimized token usage.

        This is the main entry point for agent-based task execution.
        """
        start_time = time.time()

        try:
            # Validate agent capabilities
            if not self._validate_agent_request(request):
                raise ValueError(f"Invalid request for agent {request.agent_role}")

            # Optimize the request for token efficiency
            optimization_result = await self.token_optimizer.optimize_request(
                agent_role=request.agent_role,
                prompt=request.prompt,
                context=request.context.metadata.get("context_text"),
                task_complexity=request.context.task_complexity,
                max_tokens=request.max_tokens,
            )

            # Update request with optimizations
            optimized_request = BaseAIRequest(
                prompt=optimization_result["optimized_prompt"],
                context=optimization_result.get("optimized_context"),
                max_tokens=optimization_result["estimated_tokens"],
                temperature=request.temperature,
                user_id=request.context.user_id,
                session_id=request.context.session_id,
                preferred_provider=self._get_provider_from_key(
                    optimization_result["provider_key"]
                ),
            )

            # Execute the request using the enhanced AI service
            response = await self.enhanced_ai_service.generate_quote(optimized_request)

            # Calculate actual metrics
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Record usage statistics
            usage_stats = TokenUsageStats(
                total_tokens=response.tokens_used,
                prompt_tokens=int(response.tokens_used * 0.7),  # Estimate
                completion_tokens=int(response.tokens_used * 0.3),  # Estimate
                cost_usd=response.cost,
                response_time_ms=response_time_ms,
                quality_score=response.quality_score,
            )

            await self.token_optimizer.record_usage(
                optimization_result["provider_key"], usage_stats
            )

            # Update agent metrics
            await self._update_agent_metrics(request.agent_role, usage_stats, True)

            # Calculate cost savings
            baseline_cost = await self._estimate_baseline_cost(request)
            cost_savings = max(0, baseline_cost - response.cost)

            return {
                "success": True,
                "response": {
                    "text": response.text,
                    "provider": response.provider.value,
                    "model": response.model,
                    "quality_score": response.quality_score,
                },
                "metrics": {
                    "tokens_used": response.tokens_used,
                    "cost_usd": response.cost,
                    "response_time_ms": response_time_ms,
                    "cost_savings_usd": cost_savings,
                    "token_efficiency": optimization_result["optimization_metadata"][
                        "compression_ratio"
                    ],
                },
                "agent_info": {
                    "role": request.agent_role.value,
                    "capabilities": [
                        cap.value
                        for cap in AGENT_CAPABILITIES[request.agent_role].capabilities
                    ],
                    "optimization_strategy": self.token_optimizer.strategy.value,
                },
                "request_id": request.request_id,
            }

        except Exception as e:
            # Record failure metrics
            await self._update_agent_metrics(request.agent_role, None, False)

            logger.error(f"Agent task execution failed for {request.agent_role}: {e}")

            return {
                "success": False,
                "error": str(e),
                "agent_info": {
                    "role": request.agent_role.value,
                    "capabilities": [
                        cap.value
                        for cap in AGENT_CAPABILITIES[request.agent_role].capabilities
                    ],
                },
                "request_id": request.request_id,
            }

    async def execute_multi_agent_workflow(
        self, workflow_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a complex workflow involving multiple agents.

        Example workflow: Quote Analysis -> Content Creation -> Quality Review
        """
        workflow_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Parse workflow definition
            workflow_steps = workflow_request.get("steps", [])
            if not workflow_steps:
                raise ValueError("No workflow steps provided")

            # Initialize workflow tracking
            self.workflow_metrics[workflow_id] = {
                "started_at": datetime.now(),
                "steps": len(workflow_steps),
                "completed_steps": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "agents_used": [],
            }

            workflow_results = []
            accumulated_context = workflow_request.get("initial_context", {})

            # Execute workflow steps sequentially
            for step_index, step in enumerate(workflow_steps):
                step_start_time = time.time()

                # Create agent context for this step
                agent_context = AgentContext(
                    user_id=workflow_request.get("user_id"),
                    session_id=workflow_request.get("session_id"),
                    task_complexity=TaskComplexity(step.get("complexity", "moderate")),
                    max_tokens=step.get("max_tokens", 500),
                    workflow_id=workflow_id,
                    parent_task_id=step.get("parent_task_id"),
                    metadata=accumulated_context,
                )

                # Create agent request
                agent_request = AgentRequest(
                    prompt=step["prompt"],
                    agent_role=AgentRole(step["agent_role"]),
                    context=agent_context,
                    temperature=step.get("temperature", 0.7),
                )

                # Execute step
                step_result = await self.execute_agent_task(agent_request)

                # Update workflow metrics
                if step_result["success"]:
                    self.workflow_metrics[workflow_id]["completed_steps"] += 1
                    self.workflow_metrics[workflow_id]["total_cost"] += step_result[
                        "metrics"
                    ]["cost_usd"]
                    self.workflow_metrics[workflow_id]["total_tokens"] += step_result[
                        "metrics"
                    ]["tokens_used"]
                    self.workflow_metrics[workflow_id]["agents_used"].append(
                        step["agent_role"]
                    )

                    # Update accumulated context for next step
                    accumulated_context.update(
                        {
                            f"step_{step_index}_result": step_result["response"][
                                "text"
                            ],
                            f"step_{step_index}_quality": step_result["response"][
                                "quality_score"
                            ],
                        }
                    )
                else:
                    # Workflow failed at this step
                    workflow_results.append(
                        {
                            "step": step_index,
                            "agent_role": step["agent_role"],
                            "success": False,
                            "error": step_result["error"],
                        }
                    )
                    break

                # Add step result to workflow results
                step_duration = time.time() - step_start_time
                workflow_results.append(
                    {
                        "step": step_index,
                        "agent_role": step["agent_role"],
                        "success": True,
                        "result": step_result,
                        "duration_ms": step_duration * 1000,
                    }
                )

            # Calculate final workflow metrics
            total_duration = time.time() - start_time
            workflow_success = len(
                [r for r in workflow_results if r["success"]]
            ) == len(workflow_steps)

            return {
                "workflow_id": workflow_id,
                "success": workflow_success,
                "results": workflow_results,
                "metrics": {
                    "total_duration_ms": total_duration * 1000,
                    "steps_completed": self.workflow_metrics[workflow_id][
                        "completed_steps"
                    ],
                    "total_steps": len(workflow_steps),
                    "total_cost_usd": self.workflow_metrics[workflow_id]["total_cost"],
                    "total_tokens": self.workflow_metrics[workflow_id]["total_tokens"],
                    "agents_used": self.workflow_metrics[workflow_id]["agents_used"],
                    "avg_cost_per_step": self.workflow_metrics[workflow_id][
                        "total_cost"
                    ]
                    / len(workflow_steps),
                    "cost_efficiency": self._calculate_workflow_cost_efficiency(
                        workflow_id
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Multi-agent workflow {workflow_id} failed: {e}")
            return {
                "workflow_id": workflow_id,
                "success": False,
                "error": str(e),
                "partial_results": workflow_results
                if "workflow_results" in locals()
                else [],
            }

    def _validate_agent_request(self, request: AgentRequest) -> bool:
        """Validate that the agent request is properly formed."""

        # Check if agent role exists
        if request.agent_role not in AGENT_CAPABILITIES:
            return False

        # Check if prompt is provided
        if not request.prompt or len(request.prompt.strip()) == 0:
            return False

        # Check context validity
        if not request.context:
            return False

        return True

    def _get_provider_from_key(self, provider_key: str) -> str:
        """Extract provider name from provider key."""
        return provider_key.split(":")[0] if ":" in provider_key else provider_key

    async def _estimate_baseline_cost(self, request: AgentRequest) -> float:
        """Estimate what the cost would be without optimization."""

        # Use a standard tier model as baseline
        baseline_tokens = len(request.prompt) // 3  # Rough estimate
        baseline_cost_per_1k = 0.002  # GPT-4 baseline cost

        return (baseline_tokens / 1000) * baseline_cost_per_1k

    async def _update_agent_metrics(
        self,
        agent_role: AgentRole,
        usage_stats: Optional[TokenUsageStats],
        success: bool,
    ):
        """Update performance metrics for an agent."""

        metrics = self.agent_metrics[agent_role]
        metrics["total_requests"] += 1
        metrics["last_used"] = datetime.now()

        if success and usage_stats:
            metrics["successful_requests"] += 1

            # Update moving averages (exponential moving average with alpha=0.1)
            alpha = 0.1
            metrics["avg_response_time_ms"] = (1 - alpha) * metrics[
                "avg_response_time_ms"
            ] + alpha * usage_stats.response_time_ms
            metrics["avg_cost_usd"] = (1 - alpha) * metrics[
                "avg_cost_usd"
            ] + alpha * usage_stats.cost_usd
            metrics["avg_quality_score"] = (1 - alpha) * metrics[
                "avg_quality_score"
            ] + alpha * usage_stats.quality_score
        else:
            metrics["failed_requests"] += 1

    def _calculate_workflow_cost_efficiency(self, workflow_id: str) -> float:
        """Calculate cost efficiency score for a workflow (0-1 scale)."""

        workflow_data = self.workflow_metrics.get(workflow_id)
        if not workflow_data:
            return 0.0

        # Simple efficiency calculation based on cost per successful step
        if workflow_data["completed_steps"] == 0:
            return 0.0

        cost_per_step = workflow_data["total_cost"] / workflow_data["completed_steps"]

        # Efficiency is inverse of cost, normalized (lower cost = higher efficiency)
        # Assume $0.02 per step is average, $0.001 is excellent
        normalized_efficiency = max(0, 1 - (cost_per_step / 0.02))

        return min(1.0, normalized_efficiency)

    async def get_agent_recommendations(
        self, task_description: str
    ) -> List[Dict[str, Any]]:
        """Get recommendations for which agents to use for a given task."""

        recommendations = []

        # Simple keyword-based matching for agent recommendations
        task_lower = task_description.lower()

        if any(
            word in task_lower for word in ["analyze", "review", "evaluate", "assess"]
        ):
            recommendations.append(
                {
                    "agent_role": AgentRole.QUOTE_ANALYST.value,
                    "confidence": 0.8,
                    "reason": "Task involves analysis or evaluation",
                }
            )

        if any(
            word in task_lower for word in ["generate", "create", "write", "compose"]
        ):
            recommendations.append(
                {
                    "agent_role": AgentRole.CONTENT_CREATOR.value,
                    "confidence": 0.9,
                    "reason": "Task involves content creation",
                }
            )

        if any(
            word in task_lower for word in ["voice", "audio", "transcribe", "speech"]
        ):
            recommendations.append(
                {
                    "agent_role": AgentRole.VOICE_PROCESSOR.value,
                    "confidence": 0.9,
                    "reason": "Task involves voice/audio processing",
                }
            )

        if any(
            word in task_lower
            for word in ["psychology", "emotion", "personality", "feeling"]
        ):
            recommendations.append(
                {
                    "agent_role": AgentRole.PSYCHOLOGY_ANALYZER.value,
                    "confidence": 0.8,
                    "reason": "Task involves psychological analysis",
                }
            )

        if any(word in task_lower for word in ["price", "cost", "optimize", "budget"]):
            recommendations.append(
                {
                    "agent_role": AgentRole.PRICING_OPTIMIZER.value,
                    "confidence": 0.7,
                    "reason": "Task involves pricing optimization",
                }
            )

        # Always suggest quality review for important tasks
        if any(
            word in task_lower for word in ["important", "critical", "final", "publish"]
        ):
            recommendations.append(
                {
                    "agent_role": AgentRole.QUALITY_REVIEWER.value,
                    "confidence": 0.6,
                    "reason": "Important tasks benefit from quality review",
                }
            )

        return sorted(recommendations, key=lambda x: x["confidence"], reverse=True)

    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the enhanced orchestrator."""

        # Get base AI service health
        ai_service_health = (
            await self.enhanced_ai_service.get_health_status()
            if self.enhanced_ai_service
            else {}
        )

        # Get token optimizer analysis
        cost_analysis = self.token_optimizer.get_cost_analysis()
        optimization_recommendations = self.token_optimizer.get_recommendations()

        # Calculate agent utilization
        total_agent_requests = sum(
            metrics["total_requests"] for metrics in self.agent_metrics.values()
        )
        agent_utilization = {
            role.value: {
                "requests": metrics["total_requests"],
                "success_rate": metrics["successful_requests"]
                / max(metrics["total_requests"], 1),
                "avg_cost": metrics["avg_cost_usd"],
                "avg_quality": metrics["avg_quality_score"],
            }
            for role, metrics in self.agent_metrics.items()
            if metrics["total_requests"] > 0
        }

        return {
            "orchestrator_status": "healthy",
            "ai_service_health": ai_service_health,
            "token_optimization": {
                "strategy": self.token_optimizer.strategy.value,
                "cost_analysis": cost_analysis,
                "recommendations": optimization_recommendations,
            },
            "agent_metrics": {
                "total_requests": total_agent_requests,
                "active_workflows": len(self.workflow_metrics),
                "agent_utilization": agent_utilization,
            },
            "capabilities": {
                "available_agents": [role.value for role in AgentRole],
                "available_tiers": [tier.value for tier in ProviderTier],
                "max_concurrent_agents": self.max_concurrent_agents,
            },
            "timestamp": datetime.now().isoformat(),
        }
