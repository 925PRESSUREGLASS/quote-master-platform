# Regression Map

| area | rule | named test | severity | owner | fix idea |
|------|------|------------|----------|-------|----------|
| AI orchestration | Provider fallback sequence (OpenAI→Claude) | test_ai_fallback_order | high | AI Team | enforce service order in orchestrator |
| AI orchestration | Performance score weights 0.4/0.3/0.3 | test_ai_performance_scoring_weights | medium | AI Team | refactor to constants |
| AI orchestration | Cost-optimized selection uses quality/cost | test_ai_cost_optimized_selection | medium | AI Team | document defaults and ensure config override |
| AI orchestration | Fallback executes when primary fails | test_ai_fallback_on_failure | high | AI Team | add provider health checks |
| AI orchestration | Tracing env flag toggles instrumentation | test_tracing_env_toggle | low | Infra Team | validate ENABLE_TRACING behavior |
| Quotas | Non-premium users limited to 50 quotes/day | test_daily_quote_limit_non_premium | high | Backend Team | add counter reset cron |
| Quotas | API rate limiting 60 req/min | test_rate_limit_enforced | high | Backend Team | integrate Redis token bucket |
| Quotas | Provider rate limits (OpenAI 60/min, Anthropic 50/min) | test_ai_provider_rate_limits | medium | AI Team | monitor provider quota settings |
| Quotas | Voice quota enforcement placeholder | test_voice_quota_limit | low | Backend Team | implement voice quota logic |
| Upload validation | Reject files over 10MB | test_voice_upload_rejects_large_file | high | Backend Team | streaming upload check |
| Upload validation | Reject unsupported MIME type | test_voice_upload_invalid_type | medium | Backend Team | centralize MIME list |
| Upload validation | Accept supported formats | test_voice_upload_supported_formats | low | Backend Team | extend tests for new formats |
| Auth roles | Admin endpoints require admin role | test_admin_endpoint_requires_admin_role | high | Security Team | add role-based middleware |
| Auth roles | Unverified users cannot generate quotes | test_unverified_user_cannot_generate_quote | medium | Security Team | add verification check tests |
| Rate limits | RateLimitChecker allows within limit | test_rate_limit_allows_under_threshold | medium | Backend Team | implement storage for counts |
| Rate limits | RateLimitChecker blocks over limit | test_rate_limit_blocks_over_threshold | high | Backend Team | implement 429 response |
