#!/usr/bin/env python3
"""
Test script for the Enhanced Multi-Agent AI Orchestration System

This script tests the complete multi-agent system including:
- Agent roles and capabilities
- Token optimization
- Workflow execution
- Cost monitoring
- Code generation agents
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.services.ai.agents.agent_types import AgentContext, AgentRole, TaskComplexity
from src.services.ai.agents.agent_workflows import (
    AgentWorkflowManager,
    get_workflow_manager,
)
from src.services.ai.agents.enhanced_orchestrator import (
    AgentRequest,
    EnhancedAIOrchestrator,
)
from src.services.ai.agents.monitoring import get_agent_monitor
from src.services.ai.agents.token_optimizer import TokenStrategy


async def test_agent_system():
    """Test the complete multi-agent system."""

    print("=" * 80)
    print("🤖 TESTING ENHANCED MULTI-AGENT AI ORCHESTRATION SYSTEM")
    print("=" * 80)

    try:
        # Initialize the enhanced orchestrator
        print("\n1. Initializing Enhanced AI Orchestrator...")
        orchestrator = EnhancedAIOrchestrator()
        await orchestrator.initialize()
        print("✅ Enhanced AI Orchestrator initialized successfully")

        # Initialize workflow manager
        print("\n2. Initializing Workflow Manager...")
        workflow_manager = get_workflow_manager(orchestrator)
        print("✅ Workflow Manager initialized successfully")

        # Initialize monitoring
        print("\n3. Initializing Agent Monitor...")
        monitor = get_agent_monitor()
        print("✅ Agent Monitor initialized successfully")

        # Test 1: Quote Generation Agent
        print("\n" + "=" * 50)
        print("TEST 1: Quote Generation Agent")
        print("=" * 50)

        context = AgentContext(
            user_id="test_user",
            session_id="test_session",
            task_complexity=TaskComplexity.MODERATE,
            max_tokens=300,
        )

        quote_request = AgentRequest(
            prompt="Generate an inspiring quote about perseverance and overcoming challenges",
            agent_role=AgentRole.CONTENT_CREATOR,
            context=context,
        )

        print("📝 Testing quote generation...")
        quote_result = await orchestrator.execute_agent_task(quote_request)

        if quote_result["success"]:
            print("✅ Quote Generation Test PASSED")
            print(f"📄 Generated Quote: {quote_result['response']['text']}")
            print(f"💰 Cost: ${quote_result['metrics']['cost_usd']:.4f}")
            print(f"🔢 Tokens: {quote_result['metrics']['tokens_used']}")
        else:
            print("❌ Quote Generation Test FAILED")
            print(f"Error: {quote_result['error']}")

        # Test 2: Code Generation Agent
        print("\n" + "=" * 50)
        print("TEST 2: Code Generation Agent")
        print("=" * 50)

        code_context = AgentContext(
            user_id="test_user",
            session_id="test_session",
            task_complexity=TaskComplexity.COMPLEX,
            max_tokens=800,
            metadata={"language": "python", "coding_style": "clean_code"},
        )

        code_request = AgentRequest(
            prompt="Create a Python function that calculates the Fibonacci sequence using memoization for optimization",
            agent_role=AgentRole.CODE_GENERATOR,
            context=code_context,
        )

        print("💻 Testing code generation...")
        code_result = await orchestrator.execute_agent_task(code_request)

        if code_result["success"]:
            print("✅ Code Generation Test PASSED")
            print("📄 Generated Code:")
            print("-" * 40)
            print(code_result["response"]["text"])
            print("-" * 40)
            print(f"💰 Cost: ${code_result['metrics']['cost_usd']:.4f}")
            print(f"🔢 Tokens: {code_result['metrics']['tokens_used']}")
        else:
            print("❌ Code Generation Test FAILED")
            print(f"Error: {code_result['error']}")

        # Test 3: Multi-Agent Workflow
        print("\n" + "=" * 50)
        print("TEST 3: Multi-Agent Workflow")
        print("=" * 50)

        print("📋 Available workflows:")
        workflows = workflow_manager.list_workflows()
        for workflow in workflows:
            print(f"  - {workflow['name']} ({workflow['workflow_id']})")

        print("\n🔄 Testing quote generation workflow...")
        workflow_input = {
            "input_text": "I need motivation for starting a new business venture",
            "user_id": "test_user",
            "session_id": "test_session",
        }

        execution_id = await workflow_manager.execute_workflow(
            "quote_generation_pipeline", workflow_input
        )

        print(f"🚀 Started workflow execution: {execution_id}")

        # Wait for workflow completion (with timeout)
        max_wait_seconds = 60
        wait_interval = 2
        total_waited = 0

        while total_waited < max_wait_seconds:
            status = await workflow_manager.get_execution_status(execution_id)
            if status:
                print(
                    f"⏳ Workflow Status: {status['status']} - Step {status['completed_steps']}/{status['total_steps']}"
                )

                if status["status"] in ["completed", "failed", "cancelled"]:
                    break

            await asyncio.sleep(wait_interval)
            total_waited += wait_interval

        final_status = await workflow_manager.get_execution_status(execution_id)
        if final_status:
            if final_status["status"] == "completed":
                print("✅ Multi-Agent Workflow Test PASSED")
                print(f"💰 Total Cost: ${final_status['total_cost']:.4f}")
                print(f"🔢 Total Tokens: {final_status['total_tokens']}")
                print(f"👥 Agents Used: {', '.join(final_status['agents_used'])}")
            else:
                print("❌ Multi-Agent Workflow Test FAILED")
                print(f"Final Status: {final_status['status']}")

        # Test 4: Agent Monitoring and Analytics
        print("\n" + "=" * 50)
        print("TEST 4: Monitoring & Analytics")
        print("=" * 50)

        print("📊 System Health Check...")
        health = await monitor.get_system_health()
        print(f"✅ System Status: {health['overall_status']}")
        print(f"🔢 Total Requests: {health['summary']['total_requests']}")
        print(f"📈 Success Rate: {health['summary']['overall_success_rate']:.1f}%")
        print(f"💰 Total Cost: ${health['summary']['total_cost_usd']:.4f}")

        if health["top_performing_agents"]:
            print("\n🏆 Top Performing Agents:")
            for agent in health["top_performing_agents"][:3]:
                print(f"  - {agent['agent_role']}: {agent['overall_score']:.2f} score")

        # Test 5: Token Optimization
        print("\n" + "=" * 50)
        print("TEST 5: Token Optimization")
        print("=" * 50)

        print("⚡ Testing token optimization strategies...")

        # Test different optimization strategies
        strategies = [
            TokenStrategy.COST_MINIMIZED,
            TokenStrategy.BALANCED,
            TokenStrategy.QUALITY_FIRST,
        ]

        for strategy in strategies:
            orchestrator.token_optimizer.set_strategy(strategy)

            test_request = AgentRequest(
                prompt="Generate a short motivational quote about success",
                agent_role=AgentRole.CONTENT_CREATOR,
                context=AgentContext(
                    task_complexity=TaskComplexity.SIMPLE, max_tokens=100
                ),
            )

            result = await orchestrator.execute_agent_task(test_request)

            if result["success"]:
                print(
                    f"  ✅ {strategy.value}: ${result['metrics']['cost_usd']:.4f} | {result['metrics']['tokens_used']} tokens"
                )
            else:
                print(f"  ❌ {strategy.value}: Failed")

        # Final System Status
        print("\n" + "=" * 50)
        print("FINAL SYSTEM STATUS")
        print("=" * 50)

        orchestrator_status = await orchestrator.get_orchestrator_status()
        print(f"🤖 Orchestrator Status: {orchestrator_status['orchestrator_status']}")
        print(
            f"🔢 Total Agent Requests: {orchestrator_status['agent_metrics']['total_requests']}"
        )
        print(
            f"📊 Active Workflows: {orchestrator_status['agent_metrics']['active_workflows']}"
        )
        print(
            f"🎯 Available Agents: {len(orchestrator_status['capabilities']['available_agents'])}"
        )
        print(
            f"🏗️ Available Tiers: {len(orchestrator_status['capabilities']['available_tiers'])}"
        )

        print("\n" + "=" * 80)
        print("🎉 MULTI-AGENT SYSTEM TESTING COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ SYSTEM TEST FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test execution."""

    print("Starting Multi-Agent AI System Tests...")
    print(f"Timestamp: {datetime.now().isoformat()}")

    success = await test_agent_system()

    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
