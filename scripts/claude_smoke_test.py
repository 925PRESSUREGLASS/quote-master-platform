"""
Quick Anthropic Claude smoke test to verify API key and basic generation.

Usage (PowerShell):
  $env:ANTHROPIC_API_KEY = "sk-ant-..."  # put your real key here
  python scripts/claude_smoke_test.py
"""

import asyncio
import os
import sys
from typing import Optional

from src.core.config import get_settings
from src.services.ai.base import AIResponse
from src.services.ai.claude import ClaudeService


async def run(prompt: Optional[str] = None) -> int:
    settings = get_settings()
    api_key = os.getenv("ANTHROPIC_API_KEY") or settings.anthropic_api_key

    if not api_key or api_key.startswith("your-"):
        print("Anthropic API key is not set. Set ANTHROPIC_API_KEY and retry.")
        return 1

    prompt = (
        prompt or "Write a short, original motivational quote about" " perseverance."
    )

    service = ClaudeService(
        api_key=api_key,
        model_name=settings.anthropic_model,
        timeout=20,
    )

    try:
        print("Running Claude smoke test...\n")
        resp: AIResponse = await service.generate_quote(
            prompt=prompt,
            length="short",
        )
        print("Model:", resp.model_used)
        print("Success:", resp.success)
        print("Confidence:", resp.confidence_score)
        print("Estimated cost:", resp.usage.get("estimated_cost"))
        print("\nOutput:\n" + (resp.content or "<no content>"))
        return 0 if resp.success else 2
    except Exception as e:
        print("Claude test failed:", str(e))
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(run())
    sys.exit(exit_code)
