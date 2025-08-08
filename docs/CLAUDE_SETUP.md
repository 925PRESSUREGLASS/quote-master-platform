# Claude (Anthropic) Setup Guide

This project includes built-in support for Anthropic Claude via `ClaudeService` and the enhanced AI service orchestration. Follow these steps to enable and test Claude locally.

## 1) Set your API key

- Get your key from <https://console.anthropic.com/>
- In PowerShell (Windows):

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # replace with your real key
```

Optionally, add it to a local .env file:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

## 2) Choose a model

By default, the project uses the `settings.anthropic_model` value (see `src/core/config.py`). You can change this through environment variables as needed.

Examples:

- claude-3-haiku-20240307
- claude-3-sonnet-20240229
- claude-3-opus-20240229

## 3) Quick smoke test

Run the included smoke test to verify your key and a basic generation:

```powershell
python scripts/claude_smoke_test.py
```

Expected output includes the model used, success flag, confidence score, estimated cost, and a short generated quote.

## 4) Application usage

- The enhanced AI orchestration (`src/services/ai/enhanced_ai_service.py`) will enable Claude automatically when `ANTHROPIC_API_KEY` is set.
- Standard quote generation and analysis paths can route to Claude depending on configuration and smart routing.

## Troubleshooting

- If you see an authentication error, re-check your `ANTHROPIC_API_KEY` value and that your account has access to the chosen model.
- Ensure your virtual environment has the `anthropic` package installed (it's already listed in `requirements.txt`).
- Network/firewall issues can cause timeouts.
