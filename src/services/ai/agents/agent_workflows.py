"""
Agent Workflow Manager for Multi-Agent AI Orchestration

This module provides workflow coordination, task scheduling, and pipeline management
for complex multi-agent operations in the Quote Master Pro system.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from .agent_types import AgentContext, AgentRole, TaskComplexity
from .enhanced_orchestrator import AgentRequest, EnhancedAIOrchestrator
from .monitoring import get_agent_monitor

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowStepType(str, Enum):
    """Types of workflow steps."""

    AGENT_TASK = "agent_task"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    DELAY = "delay"
    WEBHOOK = "webhook"
    TRANSFORM = "transform"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""

    step_id: str
    step_type: WorkflowStepType
    name: str

    # Agent task configuration
    agent_role: Optional[AgentRole] = None
    prompt_template: Optional[str] = None

    # Control flow
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3

    # Conditional logic
    condition: Optional[str] = None  # Python expression

    # Parallel execution
    parallel_steps: List["WorkflowStep"] = field(default_factory=list)

    # Data transformation
    transform_function: Optional[str] = None

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Runtime data
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""

    workflow_id: str
    name: str
    description: str
    version: str

    # Execution steps
    steps: List[WorkflowStep]

    # Configuration
    timeout_seconds: int = 1800  # 30 minutes default
    max_concurrent_steps: int = 5
    retry_policy: str = "exponential_backoff"

    # Triggers and scheduling
    triggers: List[str] = field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression

    # Data flow
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Runtime workflow execution instance."""

    execution_id: str
    workflow_id: str
    status: WorkflowStatus

    # Input/Output
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Results
    step_results: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)

    # Metrics
    total_cost: float = 0.0
    total_tokens: int = 0
    agents_used: List[str] = field(default_factory=list)


class AgentWorkflowManager:
    """Manages complex multi-agent workflows and task coordination."""

    def __init__(self, orchestrator: Optional[EnhancedAIOrchestrator] = None):
        self.orchestrator = orchestrator
        self.monitor = get_agent_monitor()

        # Workflow storage
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []

        # Execution control
        self.max_concurrent_workflows = 10
        self.step_executor_pool = asyncio.Semaphore(20)  # Max concurrent steps

        # Pre-defined workflows
        self._initialize_builtin_workflows()

    def _initialize_builtin_workflows(self):
        """Initialize common workflow templates."""

        # Quote Generation Workflow
        quote_workflow = WorkflowDefinition(
            workflow_id="quote_generation_pipeline",
            name="Complete Quote Generation Pipeline",
            description="End-to-end quote generation with analysis, creation, and review",
            version="1.0",
            steps=[
                WorkflowStep(
                    step_id="analyze_requirements",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Analyze Quote Requirements",
                    agent_role=AgentRole.QUOTE_ANALYST,
                    prompt_template="Analyze the following quote request and determine complexity, style, and requirements: {input_text}",
                    config={"max_tokens": 300},
                ),
                WorkflowStep(
                    step_id="generate_quote",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate Quote Content",
                    agent_role=AgentRole.CONTENT_CREATOR,
                    prompt_template="Based on the analysis: {analyze_requirements}, create a quote that meets these requirements: {input_text}",
                    depends_on=["analyze_requirements"],
                    config={"max_tokens": 500},
                ),
                WorkflowStep(
                    step_id="review_quality",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Quality Review",
                    agent_role=AgentRole.QUALITY_REVIEWER,
                    prompt_template="Review this generated quote for quality, accuracy, and appropriateness: {generate_quote}",
                    depends_on=["generate_quote"],
                    config={"max_tokens": 200},
                ),
            ],
            tags=["quote", "generation", "pipeline"],
        )

        # Voice Processing Workflow
        voice_workflow = WorkflowDefinition(
            workflow_id="voice_to_quote_pipeline",
            name="Voice-to-Quote Processing Pipeline",
            description="Process voice input through transcription, analysis, and quote generation",
            version="1.0",
            steps=[
                WorkflowStep(
                    step_id="transcribe_voice",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Voice Transcription",
                    agent_role=AgentRole.VOICE_PROCESSOR,
                    prompt_template="Transcribe and analyze the emotional context of this voice input: {voice_data}",
                    config={"max_tokens": 400},
                ),
                WorkflowStep(
                    step_id="psychological_analysis",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Psychological Profile Analysis",
                    agent_role=AgentRole.PSYCHOLOGY_ANALYZER,
                    prompt_template="Analyze the psychological profile and emotional state from this transcription: {transcribe_voice}",
                    depends_on=["transcribe_voice"],
                    config={"max_tokens": 300},
                ),
                WorkflowStep(
                    step_id="personalized_quote",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate Personalized Quote",
                    agent_role=AgentRole.CONTENT_CREATOR,
                    prompt_template="Create a personalized quote based on psychological analysis: {psychological_analysis} and original input: {transcribe_voice}",
                    depends_on=["psychological_analysis"],
                    config={"max_tokens": 500},
                ),
            ],
            tags=["voice", "psychology", "personalization"],
        )

        # Cost Optimization Workflow
        optimization_workflow = WorkflowDefinition(
            workflow_id="cost_optimization_review",
            name="Cost Optimization Review",
            description="Analyze system usage and provide cost optimization recommendations",
            version="1.0",
            steps=[
                WorkflowStep(
                    step_id="analyze_usage",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Analyze System Usage",
                    agent_role=AgentRole.COST_MONITOR,
                    prompt_template="Analyze recent system usage patterns and identify cost optimization opportunities: {usage_data}",
                    config={"max_tokens": 400},
                ),
                WorkflowStep(
                    step_id="generate_recommendations",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate Optimization Recommendations",
                    agent_role=AgentRole.TOKEN_OPTIMIZER,
                    prompt_template="Based on usage analysis: {analyze_usage}, provide specific actionable cost optimization recommendations",
                    depends_on=["analyze_usage"],
                    config={"max_tokens": 300},
                ),
            ],
            tags=["cost", "optimization", "analysis"],
        )

        # Code Development Workflow
        code_development_workflow = WorkflowDefinition(
            workflow_id="code_development_pipeline",
            name="Complete Code Development Pipeline",
            description="End-to-end code development with generation, review, and testing",
            version="1.0",
            steps=[
                WorkflowStep(
                    step_id="analyze_requirements",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Analyze Code Requirements",
                    agent_role=AgentRole.QUOTE_ANALYST,  # Can analyze requirements
                    prompt_template="Analyze the following coding requirement and determine complexity, language, architecture, and implementation approach: {requirement}",
                    config={"max_tokens": 400},
                ),
                WorkflowStep(
                    step_id="generate_code",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate Code Implementation",
                    agent_role=AgentRole.CODE_GENERATOR,
                    prompt_template="Based on the analysis: {analyze_requirements}, implement the following requirement: {requirement}. Language: {language}. Style: {coding_style}",
                    depends_on=["analyze_requirements"],
                    config={"max_tokens": 1500},
                ),
                WorkflowStep(
                    step_id="review_code",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Code Quality Review",
                    agent_role=AgentRole.CODE_REVIEWER,
                    prompt_template="Review this generated code for quality, security, performance, and best practices: {generate_code}",
                    depends_on=["generate_code"],
                    config={"max_tokens": 800},
                ),
                WorkflowStep(
                    step_id="generate_tests",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate Unit Tests",
                    agent_role=AgentRole.CODE_GENERATOR,
                    prompt_template="Generate comprehensive unit tests for this code: {generate_code}. Test framework: {test_framework}",
                    depends_on=["generate_code"],
                    config={"max_tokens": 1000},
                ),
            ],
            tags=["code", "development", "testing"],
        )

        # API Integration Workflow
        api_integration_workflow = WorkflowDefinition(
            workflow_id="api_integration_pipeline",
            name="API Integration Development",
            description="Develop API integrations with client code, error handling, and testing",
            version="1.0",
            steps=[
                WorkflowStep(
                    step_id="analyze_api",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Analyze API Documentation",
                    agent_role=AgentRole.API_INTEGRATOR,
                    prompt_template="Analyze this API documentation and determine integration requirements: {api_documentation}. Target language: {language}",
                    config={"max_tokens": 500},
                ),
                WorkflowStep(
                    step_id="generate_client",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate API Client Code",
                    agent_role=AgentRole.CODE_GENERATOR,
                    prompt_template="Generate API client code based on analysis: {analyze_api}. Include error handling, authentication, and proper data models.",
                    depends_on=["analyze_api"],
                    config={"max_tokens": 2000},
                ),
                WorkflowStep(
                    step_id="generate_integration_tests",
                    step_type=WorkflowStepType.AGENT_TASK,
                    name="Generate Integration Tests",
                    agent_role=AgentRole.CODE_GENERATOR,
                    prompt_template="Generate integration tests for this API client: {generate_client}. Include mock tests and error scenarios.",
                    depends_on=["generate_client"],
                    config={"max_tokens": 1200},
                ),
            ],
            tags=["api", "integration", "client"],
        )

        # Store workflows
        self.workflow_definitions[quote_workflow.workflow_id] = quote_workflow
        self.workflow_definitions[voice_workflow.workflow_id] = voice_workflow
        self.workflow_definitions[
            optimization_workflow.workflow_id
        ] = optimization_workflow
        self.workflow_definitions[
            code_development_workflow.workflow_id
        ] = code_development_workflow
        self.workflow_definitions[
            api_integration_workflow.workflow_id
        ] = api_integration_workflow

    async def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a new workflow definition."""

        try:
            # Validate workflow
            validation_errors = self._validate_workflow(workflow)
            if validation_errors:
                logger.error(f"Workflow validation failed: {validation_errors}")
                return False

            self.workflow_definitions[workflow.workflow_id] = workflow
            logger.info(
                f"Registered workflow: {workflow.name} (ID: {workflow.workflow_id})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.workflow_id}: {e}")
            return False

    def _validate_workflow(self, workflow: WorkflowDefinition) -> List[str]:
        """Validate workflow definition."""

        errors = []

        # Basic validation
        if not workflow.workflow_id:
            errors.append("Missing workflow_id")
        if not workflow.name:
            errors.append("Missing workflow name")
        if not workflow.steps:
            errors.append("No steps defined")

        # Step validation
        step_ids = set()
        for step in workflow.steps:
            if not step.step_id:
                errors.append("Step missing step_id")
            elif step.step_id in step_ids:
                errors.append(f"Duplicate step_id: {step.step_id}")
            else:
                step_ids.add(step.step_id)

            # Dependency validation
            for dep in step.depends_on:
                if dep not in step_ids and dep not in [
                    s.step_id for s in workflow.steps
                ]:
                    errors.append(
                        f"Step {step.step_id} depends on non-existent step: {dep}"
                    )

            # Agent role validation for agent tasks
            if step.step_type == WorkflowStepType.AGENT_TASK:
                if not step.agent_role:
                    errors.append(f"Agent task step {step.step_id} missing agent_role")
                if not step.prompt_template:
                    errors.append(
                        f"Agent task step {step.step_id} missing prompt_template"
                    )

        return errors

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Execute a workflow and return execution ID."""

        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Check concurrent execution limit
        if len(self.active_executions) >= self.max_concurrent_workflows:
            raise RuntimeError("Maximum concurrent workflows exceeded")

        # Create execution instance
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            input_data=input_data,
            context=context or {},
            start_time=datetime.now(),
        )

        self.active_executions[execution_id] = execution

        # Start execution
        asyncio.create_task(self._execute_workflow_steps(execution_id))

        logger.info(
            f"Started workflow execution: {execution_id} for workflow: {workflow_id}"
        )
        return execution_id

    async def _execute_workflow_steps(self, execution_id: str):
        """Execute all steps in a workflow."""

        execution = self.active_executions[execution_id]
        workflow = self.workflow_definitions[execution.workflow_id]

        try:
            execution.status = WorkflowStatus.RUNNING

            # Create dependency graph
            dependency_graph = self._build_dependency_graph(workflow.steps)

            # Execute steps in dependency order
            await self._execute_steps_with_dependencies(
                execution, workflow, dependency_graph
            )

            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()

            logger.info(f"Workflow execution {execution_id} completed successfully")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
            execution.error_log.append(str(e))

            logger.error(f"Workflow execution {execution_id} failed: {e}")

        finally:
            # Move to history and cleanup
            self.execution_history.append(execution)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    def _build_dependency_graph(
        self, steps: List[WorkflowStep]
    ) -> Dict[str, List[str]]:
        """Build a dependency graph from workflow steps."""

        graph = {}
        for step in steps:
            graph[step.step_id] = step.depends_on.copy()

        return graph

    async def _execute_steps_with_dependencies(
        self,
        execution: WorkflowExecution,
        workflow: WorkflowDefinition,
        dependency_graph: Dict[str, List[str]],
    ):
        """Execute steps respecting dependency constraints."""

        steps_by_id = {step.step_id: step for step in workflow.steps}
        completed_steps = set()
        running_tasks = {}

        while len(completed_steps) < len(workflow.steps):
            # Find steps ready to execute
            ready_steps = []
            for step_id, dependencies in dependency_graph.items():
                if (
                    step_id not in completed_steps
                    and step_id not in running_tasks
                    and all(dep in completed_steps for dep in dependencies)
                ):
                    ready_steps.append(step_id)

            if not ready_steps and not running_tasks:
                # No steps ready and none running - possible circular dependency
                remaining_steps = set(dependency_graph.keys()) - completed_steps
                raise RuntimeError(
                    f"Circular dependency or unresolvable dependencies: {remaining_steps}"
                )

            # Start execution of ready steps
            for step_id in ready_steps:
                if len(running_tasks) < workflow.max_concurrent_steps:
                    step = steps_by_id[step_id]
                    task = asyncio.create_task(
                        self._execute_single_step(execution, step)
                    )
                    running_tasks[step_id] = task

            # Wait for at least one task to complete
            if running_tasks:
                done_tasks, _ = await asyncio.wait(
                    running_tasks.values(), return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for task in done_tasks:
                    # Find which step completed
                    completed_step_id = None
                    for step_id, step_task in running_tasks.items():
                        if step_task == task:
                            completed_step_id = step_id
                            break

                    if completed_step_id:
                        try:
                            result = await task
                            execution.step_results[completed_step_id] = result
                            execution.completed_steps.append(completed_step_id)
                            completed_steps.add(completed_step_id)

                            logger.debug(
                                f"Step {completed_step_id} completed in execution {execution.execution_id}"
                            )

                        except Exception as e:
                            execution.failed_steps.append(completed_step_id)
                            execution.error_log.append(
                                f"Step {completed_step_id} failed: {str(e)}"
                            )

                            # Check if this step is critical (has dependents)
                            has_dependents = any(
                                completed_step_id in deps
                                for deps in dependency_graph.values()
                            )

                            if has_dependents:
                                raise RuntimeError(
                                    f"Critical step {completed_step_id} failed, aborting workflow"
                                )

                            logger.warning(
                                f"Non-critical step {completed_step_id} failed, continuing"
                            )

                        finally:
                            del running_tasks[completed_step_id]

    async def _execute_single_step(
        self, execution: WorkflowExecution, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""

        async with self.step_executor_pool:
            step.status = WorkflowStatus.RUNNING
            step.start_time = datetime.now()

            try:
                execution.current_step = step.step_id

                if step.step_type == WorkflowStepType.AGENT_TASK:
                    result = await self._execute_agent_task_step(execution, step)
                elif step.step_type == WorkflowStepType.DELAY:
                    result = await self._execute_delay_step(step)
                elif step.step_type == WorkflowStepType.CONDITIONAL:
                    result = await self._execute_conditional_step(execution, step)
                elif step.step_type == WorkflowStepType.TRANSFORM:
                    result = await self._execute_transform_step(execution, step)
                else:
                    raise ValueError(f"Unsupported step type: {step.step_type}")

                step.status = WorkflowStatus.COMPLETED
                step.result = result
                step.end_time = datetime.now()

                return result

            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = str(e)
                step.end_time = datetime.now()
                raise

            finally:
                execution.current_step = None

    async def _execute_agent_task_step(
        self, execution: WorkflowExecution, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute an agent task step."""

        if not self.orchestrator:
            raise RuntimeError("No orchestrator available for agent tasks")

        # Prepare prompt from template
        prompt = self._render_prompt_template(step.prompt_template, execution)

        # Create agent context
        context = AgentContext(
            user_id=execution.context.get("user_id"),
            session_id=execution.context.get("session_id"),
            task_complexity=TaskComplexity(step.config.get("complexity", "moderate")),
            max_tokens=step.config.get("max_tokens", 500),
            workflow_id=execution.execution_id,
            parent_task_id=step.step_id,
            metadata=execution.context,
        )

        # Create agent request
        agent_request = AgentRequest(
            prompt=prompt,
            agent_role=step.agent_role,
            context=context,
            temperature=step.config.get("temperature", 0.7),
        )

        # Execute with timeout
        result = await asyncio.wait_for(
            self.orchestrator.execute_agent_task(agent_request),
            timeout=step.timeout_seconds,
        )

        # Update execution metrics
        if result.get("success"):
            metrics = result.get("metrics", {})
            execution.total_cost += metrics.get("cost_usd", 0)
            execution.total_tokens += metrics.get("tokens_used", 0)
            if step.agent_role.value not in execution.agents_used:
                execution.agents_used.append(step.agent_role.value)

        return result

    async def _execute_delay_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a delay step."""

        delay_seconds = step.config.get("delay_seconds", 1)
        await asyncio.sleep(delay_seconds)

        return {"delayed_seconds": delay_seconds}

    async def _execute_conditional_step(
        self, execution: WorkflowExecution, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute a conditional step."""

        condition = step.condition
        if not condition:
            raise ValueError("Conditional step missing condition")

        # Simple condition evaluation (you might want to use a safer evaluator)
        context_vars = {
            "input_data": execution.input_data,
            "context": execution.context,
            "step_results": execution.step_results,
        }

        try:
            condition_result = eval(condition, {"__builtins__": {}}, context_vars)
            return {"condition_met": bool(condition_result)}
        except Exception as e:
            raise ValueError(f"Condition evaluation failed: {e}")

    async def _execute_transform_step(
        self, execution: WorkflowExecution, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute a data transformation step."""

        transform_function = step.transform_function
        if not transform_function:
            raise ValueError("Transform step missing transform_function")

        # Simple transformation (you might want to use a safer approach)
        context_vars = {
            "input_data": execution.input_data,
            "context": execution.context,
            "step_results": execution.step_results,
        }

        try:
            # For safety, only allow basic transformations
            result = eval(transform_function, {"__builtins__": {}}, context_vars)
            return {"transformed_data": result}
        except Exception as e:
            raise ValueError(f"Transform function failed: {e}")

    def _render_prompt_template(
        self, template: str, execution: WorkflowExecution
    ) -> str:
        """Render a prompt template with execution context."""

        # Simple template rendering
        context = {
            **execution.input_data,
            **execution.context,
            **execution.step_results,
        }

        try:
            return template.format(**context)
        except KeyError as e:
            # If a key is missing, try to render with partial context
            logger.warning(f"Template key missing: {e}, using partial rendering")
            return template.format_map(context)

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution."""

        execution = self.active_executions.get(execution_id)
        if not execution:
            # Check history
            execution = next(
                (e for e in self.execution_history if e.execution_id == execution_id),
                None,
            )

        if not execution:
            return None

        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "completed_steps": len(execution.completed_steps),
            "failed_steps": len(execution.failed_steps),
            "total_steps": len(self.workflow_definitions[execution.workflow_id].steps),
            "start_time": execution.start_time.isoformat()
            if execution.start_time
            else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "total_cost": execution.total_cost,
            "total_tokens": execution.total_tokens,
            "agents_used": execution.agents_used,
            "error_count": len(execution.error_log),
        }

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""

        if execution_id not in self.active_executions:
            return False

        execution = self.active_executions[execution_id]
        execution.status = WorkflowStatus.CANCELLED
        execution.end_time = datetime.now()

        logger.info(f"Cancelled workflow execution: {execution_id}")
        return True

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows."""

        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "version": wf.version,
                "steps": len(wf.steps),
                "tags": wf.tags,
                "created_at": wf.created_at.isoformat(),
            }
            for wf in self.workflow_definitions.values()
        ]

    def list_active_executions(self) -> List[Dict[str, Any]]:
        """List all active workflow executions."""

        return [
            {
                "execution_id": exec.execution_id,
                "workflow_id": exec.workflow_id,
                "status": exec.status.value,
                "current_step": exec.current_step,
                "progress": f"{len(exec.completed_steps)}/{len(self.workflow_definitions[exec.workflow_id].steps)}",
                "start_time": exec.start_time.isoformat() if exec.start_time else None,
                "total_cost": exec.total_cost,
            }
            for exec in self.active_executions.values()
        ]

    async def get_workflow_analytics(
        self, workflow_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a specific workflow."""

        if workflow_id not in self.workflow_definitions:
            return {"error": f"Workflow {workflow_id} not found"}

        # Filter executions from history
        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_executions = [
            e
            for e in self.execution_history
            if e.workflow_id == workflow_id
            and e.start_time
            and e.start_time >= cutoff_date
        ]

        if not relevant_executions:
            return {
                "message": f"No executions found for {workflow_id} in the last {days} days"
            }

        # Calculate analytics
        total_executions = len(relevant_executions)
        successful_executions = len(
            [e for e in relevant_executions if e.status == WorkflowStatus.COMPLETED]
        )
        failed_executions = len(
            [e for e in relevant_executions if e.status == WorkflowStatus.FAILED]
        )

        total_cost = sum(e.total_cost for e in relevant_executions)
        total_tokens = sum(e.total_tokens for e in relevant_executions)

        # Duration analytics
        completed_executions = [
            e for e in relevant_executions if e.end_time and e.start_time
        ]
        if completed_executions:
            durations = [
                (e.end_time - e.start_time).total_seconds()
                for e in completed_executions
            ]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0

        return {
            "workflow_id": workflow_id,
            "analysis_period_days": days,
            "execution_metrics": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": (successful_executions / total_executions * 100)
                if total_executions > 0
                else 0,
            },
            "cost_metrics": {
                "total_cost_usd": total_cost,
                "avg_cost_per_execution": total_cost / total_executions
                if total_executions > 0
                else 0,
            },
            "performance_metrics": {
                "avg_duration_seconds": avg_duration,
                "min_duration_seconds": min_duration,
                "max_duration_seconds": max_duration,
                "total_tokens": total_tokens,
                "avg_tokens_per_execution": total_tokens / total_executions
                if total_executions > 0
                else 0,
            },
        }


# Global workflow manager instance
_workflow_manager = None


def get_workflow_manager(
    orchestrator: Optional[EnhancedAIOrchestrator] = None,
) -> AgentWorkflowManager:
    """Get the global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = AgentWorkflowManager(orchestrator)
    return _workflow_manager
