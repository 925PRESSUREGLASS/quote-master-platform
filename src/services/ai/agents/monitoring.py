"""
Agent Monitoring System for Multi-Agent AI Orchestration

This module provides comprehensive monitoring capabilities for agent performance,
cost tracking, quality metrics, and system health.
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

from .agent_types import AgentRole, TaskComplexity, ProviderTier, AGENT_CAPABILITIES
from .token_optimizer import TokenUsageStats

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for a specific agent."""
    
    agent_role: AgentRole
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Timing metrics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    
    # Cost metrics
    total_cost_usd: float = 0.0
    avg_cost_per_request: float = 0.0
    cost_by_provider: Dict[str, float] = None
    
    # Quality metrics
    avg_quality_score: float = 0.0
    quality_scores: List[float] = None
    
    # Token efficiency metrics
    total_tokens: int = 0
    avg_tokens_per_request: float = 0.0
    token_efficiency_score: float = 0.0
    
    # Time tracking
    first_request_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None
    active_requests: int = 0
    
    def __post_init__(self):
        if self.cost_by_provider is None:
            self.cost_by_provider = {}
        if self.quality_scores is None:
            self.quality_scores = []
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.successful_requests / max(self.total_requests, 1)) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        return (self.failed_requests / max(self.total_requests, 1)) * 100
    
    @property
    def requests_per_hour(self) -> float:
        """Calculate requests per hour based on time span."""
        if not self.first_request_time or not self.last_request_time:
            return 0.0
        
        time_span = self.last_request_time - self.first_request_time
        hours = max(time_span.total_seconds() / 3600, 1/3600)  # At least 1 second
        return self.total_requests / hours


@dataclass
class SystemHealthMetrics:
    """Overall system health metrics."""
    
    timestamp: datetime
    total_active_agents: int
    total_requests: int
    overall_success_rate: float
    avg_response_time_ms: float
    total_cost_usd: float
    
    # Resource utilization
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Provider health
    provider_health: Dict[str, str] = None
    
    # Alert conditions
    alerts: List[str] = None
    
    def __post_init__(self):
        if self.provider_health is None:
            self.provider_health = {}
        if self.alerts is None:
            self.alerts = []


class AgentMonitor:
    """Comprehensive monitoring system for multi-agent orchestration."""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        
        # Performance tracking
        self.agent_metrics: Dict[AgentRole, AgentPerformanceMetrics] = {}
        self.request_history: deque = deque(maxlen=max_history_size)
        self.system_health_history: deque = deque(maxlen=1000)
        
        # Real-time tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.provider_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "avg_response_time": 0.0,
            "success_rate": 1.0
        })
        
        # Alert thresholds
        self.alert_thresholds = {
            "max_response_time_ms": 10000,  # 10 seconds
            "min_success_rate": 0.95,       # 95%
            "max_cost_per_hour": 10.0,      # $10/hour
            "max_failure_rate": 0.05        # 5%
        }
        
        # Initialize metrics for all agent roles
        self._initialize_agent_metrics()
    
    def _initialize_agent_metrics(self):
        """Initialize performance metrics for all agent roles."""
        for role in AgentRole:
            self.agent_metrics[role] = AgentPerformanceMetrics(agent_role=role)
    
    async def start_request_tracking(self, request_id: str, agent_role: AgentRole, 
                                   provider_key: str, estimated_cost: float) -> None:
        """Start tracking a new agent request."""
        
        self.active_requests[request_id] = {
            "agent_role": agent_role,
            "provider_key": provider_key,
            "estimated_cost": estimated_cost,
            "start_time": time.time(),
            "timestamp": datetime.now()
        }
        
        # Increment active request counter
        metrics = self.agent_metrics[agent_role]
        metrics.active_requests += 1
    
    async def complete_request_tracking(self, request_id: str, success: bool,
                                      usage_stats: Optional[TokenUsageStats] = None,
                                      quality_score: Optional[float] = None) -> None:
        """Complete tracking for a request."""
        
        if request_id not in self.active_requests:
            logger.warning(f"Request {request_id} not found in active tracking")
            return
        
        request_data = self.active_requests.pop(request_id)
        
        agent_role = request_data["agent_role"]
        provider_key = request_data["provider_key"]
        start_time = request_data["start_time"]
        estimated_cost = request_data["estimated_cost"]
        
        # Calculate metrics
        response_time_ms = (time.time() - start_time) * 1000
        actual_cost = usage_stats.cost_usd if usage_stats else estimated_cost
        tokens_used = usage_stats.total_tokens if usage_stats else 0
        final_quality_score = quality_score or (usage_stats.quality_score if usage_stats else 0.0)
        
        # Update agent metrics
        await self._update_agent_metrics(
            agent_role, success, response_time_ms, actual_cost, 
            tokens_used, final_quality_score, provider_key
        )
        
        # Update provider usage
        self._update_provider_metrics(provider_key, success, response_time_ms, actual_cost, tokens_used)
        
        # Store request in history
        self.request_history.append({
            "request_id": request_id,
            "agent_role": agent_role.value,
            "provider_key": provider_key,
            "success": success,
            "response_time_ms": response_time_ms,
            "cost_usd": actual_cost,
            "tokens_used": tokens_used,
            "quality_score": final_quality_score,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _update_agent_metrics(self, agent_role: AgentRole, success: bool,
                                  response_time_ms: float, cost: float,
                                  tokens: int, quality_score: float, provider_key: str):
        """Update performance metrics for an agent."""
        
        metrics = self.agent_metrics[agent_role]
        
        # Update counters
        metrics.total_requests += 1
        metrics.active_requests = max(0, metrics.active_requests - 1)
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update timing
        current_time = datetime.now()
        if metrics.first_request_time is None:
            metrics.first_request_time = current_time
        metrics.last_request_time = current_time
        
        if success:
            # Update averages using exponential moving average
            alpha = 0.1  # Learning rate
            
            metrics.avg_response_time_ms = (
                (1 - alpha) * metrics.avg_response_time_ms + 
                alpha * response_time_ms
            )
            
            metrics.avg_cost_per_request = (
                (1 - alpha) * metrics.avg_cost_per_request +
                alpha * cost
            )
            
            metrics.avg_tokens_per_request = (
                (1 - alpha) * metrics.avg_tokens_per_request +
                alpha * tokens
            )
            
            metrics.avg_quality_score = (
                (1 - alpha) * metrics.avg_quality_score +
                alpha * quality_score
            )
            
            # Update min/max response times
            metrics.min_response_time_ms = min(metrics.min_response_time_ms, response_time_ms)
            metrics.max_response_time_ms = max(metrics.max_response_time_ms, response_time_ms)
            
            # Update cost tracking
            metrics.total_cost_usd += cost
            provider = provider_key.split(':')[0] if ':' in provider_key else provider_key
            if provider not in metrics.cost_by_provider:
                metrics.cost_by_provider[provider] = 0.0
            metrics.cost_by_provider[provider] += cost
            
            # Update token tracking
            metrics.total_tokens += tokens
            
            # Update quality scores (keep recent history)
            metrics.quality_scores.append(quality_score)
            if len(metrics.quality_scores) > 100:  # Keep last 100 scores
                metrics.quality_scores.pop(0)
            
            # Calculate token efficiency (quality per token)
            if tokens > 0:
                efficiency = quality_score / tokens * 1000  # Per 1K tokens
                metrics.token_efficiency_score = (
                    (1 - alpha) * metrics.token_efficiency_score + alpha * efficiency
                )
    
    def _update_provider_metrics(self, provider_key: str, success: bool,
                               response_time_ms: float, cost: float, tokens: int):
        """Update provider-specific metrics."""
        
        provider_stats = self.provider_usage[provider_key]
        
        provider_stats["requests"] += 1
        
        if success:
            # Update averages
            alpha = 0.1
            provider_stats["avg_response_time"] = (
                (1 - alpha) * provider_stats["avg_response_time"] +
                alpha * response_time_ms
            )
            
            provider_stats["cost"] += cost
            provider_stats["tokens"] += tokens
            
            # Update success rate
            current_successes = provider_stats["success_rate"] * (provider_stats["requests"] - 1)
            provider_stats["success_rate"] = (current_successes + 1) / provider_stats["requests"]
        else:
            # Update failure rate
            current_successes = provider_stats["success_rate"] * (provider_stats["requests"] - 1)
            provider_stats["success_rate"] = current_successes / provider_stats["requests"]
    
    async def get_agent_performance(self, agent_role: AgentRole) -> Dict[str, Any]:
        """Get comprehensive performance data for a specific agent."""
        
        metrics = self.agent_metrics.get(agent_role)
        if not metrics:
            return {"error": f"No metrics found for agent {agent_role.value}"}
        
        return {
            "agent_role": agent_role.value,
            "basic_metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "failure_rate": metrics.failure_rate,
                "active_requests": metrics.active_requests
            },
            "performance_metrics": {
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "min_response_time_ms": metrics.min_response_time_ms if metrics.min_response_time_ms != float('inf') else 0,
                "max_response_time_ms": metrics.max_response_time_ms,
                "requests_per_hour": metrics.requests_per_hour
            },
            "cost_metrics": {
                "total_cost_usd": metrics.total_cost_usd,
                "avg_cost_per_request": metrics.avg_cost_per_request,
                "cost_by_provider": dict(metrics.cost_by_provider)
            },
            "quality_metrics": {
                "avg_quality_score": metrics.avg_quality_score,
                "quality_trend": metrics.quality_scores[-10:] if metrics.quality_scores else [],
                "token_efficiency_score": metrics.token_efficiency_score
            },
            "token_metrics": {
                "total_tokens": metrics.total_tokens,
                "avg_tokens_per_request": metrics.avg_tokens_per_request
            },
            "time_span": {
                "first_request": metrics.first_request_time.isoformat() if metrics.first_request_time else None,
                "last_request": metrics.last_request_time.isoformat() if metrics.last_request_time else None
            }
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        
        current_time = datetime.now()
        
        # Aggregate metrics across all agents
        total_requests = sum(m.total_requests for m in self.agent_metrics.values())
        total_successful = sum(m.successful_requests for m in self.agent_metrics.values())
        total_cost = sum(m.total_cost_usd for m in self.agent_metrics.values())
        total_active = sum(m.active_requests for m in self.agent_metrics.values())
        
        # Calculate weighted average response time
        weighted_response_time = 0.0
        total_weight = 0
        for metrics in self.agent_metrics.values():
            if metrics.successful_requests > 0:
                weight = metrics.successful_requests
                weighted_response_time += metrics.avg_response_time_ms * weight
                total_weight += weight
        
        avg_response_time = weighted_response_time / max(total_weight, 1)
        overall_success_rate = (total_successful / max(total_requests, 1)) * 100
        
        # Check for alert conditions
        alerts = self._check_alert_conditions(avg_response_time, overall_success_rate, total_cost)
        
        # Provider health summary
        provider_health = {}
        for provider_key, stats in self.provider_usage.items():
            if stats["requests"] > 0:
                health_score = stats["success_rate"] * (1 - min(stats["avg_response_time"] / 10000, 1))
                if health_score > 0.8:
                    status = "healthy"
                elif health_score > 0.5:
                    status = "degraded"
                else:
                    status = "unhealthy"
                provider_health[provider_key] = status
        
        health_data = {
            "timestamp": current_time.isoformat(),
            "overall_status": "healthy" if not alerts else "degraded",
            "summary": {
                "total_active_agents": len([m for m in self.agent_metrics.values() if m.active_requests > 0]),
                "total_requests": total_requests,
                "overall_success_rate": overall_success_rate,
                "avg_response_time_ms": avg_response_time,
                "total_cost_usd": total_cost,
                "active_requests": total_active
            },
            "provider_health": provider_health,
            "alerts": alerts,
            "top_performing_agents": self._get_top_performers(5),
            "resource_usage": {
                "request_history_size": len(self.request_history),
                "active_tracking_size": len(self.active_requests)
            }
        }
        
        # Store in health history
        self.system_health_history.append(health_data)
        
        return health_data
    
    def _check_alert_conditions(self, avg_response_time: float, 
                              success_rate: float, total_cost: float) -> List[str]:
        """Check for alert conditions based on thresholds."""
        
        alerts = []
        
        if avg_response_time > self.alert_thresholds["max_response_time_ms"]:
            alerts.append(f"High average response time: {avg_response_time:.1f}ms")
        
        if success_rate < self.alert_thresholds["min_success_rate"] * 100:
            alerts.append(f"Low success rate: {success_rate:.1f}%")
        
        # Check hourly cost (estimate based on recent activity)
        recent_requests = [r for r in self.request_history 
                          if datetime.fromisoformat(r["timestamp"]) > datetime.now() - timedelta(hours=1)]
        hourly_cost = sum(r.get("cost_usd", 0) for r in recent_requests)
        
        if hourly_cost > self.alert_thresholds["max_cost_per_hour"]:
            alerts.append(f"High hourly cost: ${hourly_cost:.2f}")
        
        return alerts
    
    def _get_top_performers(self, limit: int) -> List[Dict[str, Any]]:
        """Get top performing agents by overall score."""
        
        performers = []
        
        for role, metrics in self.agent_metrics.items():
            if metrics.total_requests > 0:
                # Calculate overall performance score
                success_score = metrics.success_rate / 100
                speed_score = 1 / (metrics.avg_response_time_ms / 1000 + 0.1)
                quality_score = metrics.avg_quality_score
                efficiency_score = metrics.token_efficiency_score / 10  # Normalize
                
                overall_score = (
                    success_score * 0.3 +
                    min(speed_score, 1) * 0.2 +
                    quality_score * 0.3 +
                    min(efficiency_score, 1) * 0.2
                )
                
                performers.append({
                    "agent_role": role.value,
                    "overall_score": overall_score,
                    "success_rate": metrics.success_rate,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "avg_quality_score": metrics.avg_quality_score,
                    "requests_handled": metrics.total_requests
                })
        
        return sorted(performers, key=lambda x: x["overall_score"], reverse=True)[:limit]
    
    async def get_cost_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed cost analysis for the specified time period."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_requests = [
            r for r in self.request_history 
            if datetime.fromisoformat(r["timestamp"]) >= cutoff_time
        ]
        
        if not recent_requests:
            return {"error": f"No requests found in the last {hours} hours"}
        
        # Analyze costs by agent
        agent_costs = defaultdict(float)
        agent_requests = defaultdict(int)
        
        # Analyze costs by provider
        provider_costs = defaultdict(float)
        provider_requests = defaultdict(int)
        
        total_cost = 0.0
        for request in recent_requests:
            cost = request.get("cost_usd", 0)
            agent = request["agent_role"]
            provider = request["provider_key"]
            
            total_cost += cost
            agent_costs[agent] += cost
            agent_requests[agent] += 1
            provider_costs[provider] += cost
            provider_requests[provider] += 1
        
        # Calculate cost efficiency
        avg_cost_per_request = total_cost / len(recent_requests)
        projected_daily_cost = (total_cost / hours) * 24
        
        return {
            "time_period_hours": hours,
            "total_requests": len(recent_requests),
            "total_cost_usd": total_cost,
            "avg_cost_per_request": avg_cost_per_request,
            "projected_daily_cost": projected_daily_cost,
            "cost_by_agent": dict(agent_costs),
            "cost_by_provider": dict(provider_costs),
            "requests_by_agent": dict(agent_requests),
            "requests_by_provider": dict(provider_requests),
            "cost_efficiency_score": self._calculate_cost_efficiency(recent_requests),
            "recommendations": self._get_cost_recommendations(agent_costs, provider_costs)
        }
    
    def _calculate_cost_efficiency(self, requests: List[Dict]) -> float:
        """Calculate overall cost efficiency score (0-1)."""
        
        if not requests:
            return 0.0
        
        # Calculate quality-adjusted cost efficiency
        total_quality_cost_ratio = 0.0
        count = 0
        
        for request in requests:
            cost = request.get("cost_usd", 0)
            quality = request.get("quality_score", 0)
            
            if cost > 0 and quality > 0:
                efficiency = quality / cost  # Quality per dollar
                total_quality_cost_ratio += efficiency
                count += 1
        
        if count == 0:
            return 0.0
        
        avg_efficiency = total_quality_cost_ratio / count
        
        # Normalize to 0-1 scale (assume 100 quality/dollar is excellent)
        return min(avg_efficiency / 100, 1.0)
    
    def _get_cost_recommendations(self, agent_costs: Dict, provider_costs: Dict) -> List[str]:
        """Generate cost optimization recommendations."""
        
        recommendations = []
        
        # Find most expensive agents
        if agent_costs:
            most_expensive_agent = max(agent_costs.items(), key=lambda x: x[1])
            if most_expensive_agent[1] > 1.0:  # More than $1
                recommendations.append(
                    f"Consider optimizing {most_expensive_agent[0]} agent (${most_expensive_agent[1]:.2f} total cost)"
                )
        
        # Find most expensive providers
        if provider_costs:
            most_expensive_provider = max(provider_costs.items(), key=lambda x: x[1])
            if most_expensive_provider[1] > 0.5:  # More than $0.50
                recommendations.append(
                    f"High usage on {most_expensive_provider[0]} (${most_expensive_provider[1]:.2f}), consider load balancing"
                )
        
        return recommendations
    
    async def export_metrics(self, format_type: str = "json") -> str:
        """Export all metrics in the specified format."""
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "agent_metrics": {},
            "system_health": await self.get_system_health(),
            "request_history_sample": list(self.request_history)[-100:],  # Last 100 requests
            "provider_usage": dict(self.provider_usage)
        }
        
        # Export agent metrics
        for role, metrics in self.agent_metrics.items():
            export_data["agent_metrics"][role.value] = await self.get_agent_performance(role)
        
        if format_type.lower() == "json":
            return json.dumps(export_data, indent=2, default=str)
        else:
            return str(export_data)  # Fallback to string representation


# Global monitor instance
_agent_monitor = None


def get_agent_monitor() -> AgentMonitor:
    """Get the global agent monitor instance."""
    global _agent_monitor
    if _agent_monitor is None:
        _agent_monitor = AgentMonitor()
    return _agent_monitor