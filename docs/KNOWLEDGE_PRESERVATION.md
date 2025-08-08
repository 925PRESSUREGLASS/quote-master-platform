# Knowledge Preservation

## Auth
- src/api/routers/auth.py:81 - TODO: Send verification email
- src/api/routers/auth.py:111-117 - Magic numbers: access token expires in 30 minutes, refresh token 7 days, `remember_me` extends to 7/30 days
- src/api/routers/auth.py:213-214 - TODO: Store reset token and send password reset email
- src/api/routers/auth.py:217-218 - Feature flag: `settings.is_development` returns reset token for demo
- src/api/routers/auth.py:231 - TODO: Verify reset token from storage
- src/api/routers/auth.py:275 - TODO: Generate and send verification email
- src/api/routers/auth.py:288 - TODO: Verify the verification token

**Undocumented rules**
- src/api/routers/auth.py:220 - Always return success on password reset to prevent email enumeration

**Must-preserve**
- Password reset hides email existence — regression test `test_password_reset_no_enumeration`
- "Remember me" extends token lifetimes — regression test `test_login_remember_me_extends_tokens`

## Quotes
- src/api/routers/quotes.py:60 - TODO: Implement AI quote generation
- src/api/routers/quotes.py:111-113 - Magic numbers: pagination limit default 20, max 100
- src/api/routers/quotes.py:194 - TODO: Implement tag filtering with JSONB
- src/api/routers/quotes.py:499 - TODO: Prevent double-likes
- src/api/routers/quotes.py:530 - TODO: Implement AI analysis for quotes
- src/api/routers/quotes.py:203-216 - Sentiment range mapping (positive 0.1 ≤ x ≤ 1.0, negative -1.0 ≤ x ≤ -0.1, neutral -0.1 < x < 0.1)

**Undocumented rules**
- Sentiment filter uses predefined score ranges for search results

**Must-preserve**
- Sentiment range mapping for quote search — regression test `test_quote_search_sentiment_ranges`
- Pagination limits enforce 0 ≤ limit ≤ 100 — regression test `test_quote_list_pagination_limits`

## Voice
- src/api/routers/voice.py:65-76 - Validate `settings.allowed_file_types`; reject files over `settings.max_file_size`
- src/api/routers/voice.py:137 & 450 - Magic numbers: pagination limit default 20, max 100
- src/api/routers/voice.py:600 - Processing success rate = processed/total*100
- src/api/routers/voice.py:647 - TODO: Implement audio processing
- src/api/routers/voice.py:656 - TODO: Implement job processing

**Undocumented rules**
- File uploads must match allowed MIME types and size; processing statistics computed as processed/total*100

**Must-preserve**
- Reject oversized uploads — regression test `test_voice_upload_rejects_large_file`
- Reject unsupported file types — regression test `test_voice_upload_invalid_type`
- Statistics reflect accurate success rate — regression test `test_voice_processing_statistics`

## AI
- src/services/ai/orchestrator.py:52-76 - Provider initialization order (OpenAI GPT-4 → GPT-3.5 → Claude Sonnet → Claude Haiku)
- src/services/ai/orchestrator.py:197-208 - Performance score = success_rate*SUCCESS_RATE_WEIGHT + response_time_score*RESPONSE_TIME_WEIGHT + quality_score*QUALITY_SCORE_WEIGHT (30s max response)
- src/services/ai/orchestrator.py:219-234 - Cost optimization uses quality/cost with defaults cost=0.01, quality=0.5
- src/services/ai/orchestrator.py:254-266 - Fallback iterates over healthy services in insertion order
- src/services/ai/orchestrator.py:43 - Feature flag: `fallback_enabled` defaults True
- src/services/ai/monitoring/tracing.py:57,66-69,276 - Env fallbacks for HOSTNAME, `USE_OTLP_COLLECTOR`/`OTLP_ENDPOINT`, and `ENABLE_TRACING`

**Undocumented rules**
- Deterministic provider fallback order and weighted performance scoring
- Cost-optimized routing favors cheapest model for simple tasks

**Must-preserve**
- Provider fallback sequence — regression test `test_ai_fallback_order`
- Performance scoring weights — regression test `test_ai_performance_scoring_weights`
- Cost-based routing for simple tasks — regression test `test_ai_cost_optimized_selection`
- Fallback executes when primary fails — regression test `test_ai_fallback_on_failure`

## Admin
- src/api/routers/admin.py:63-65 - TODO: Implement DB, Redis, and AI health checks
- src/api/routers/admin.py:523 - Magic numbers: report days default 30, max 365
- src/api/routers/admin.py:542 - TODO: Implement retention calculation
- src/api/routers/admin.py:552 - TODO: Implement retention cohorts
- src/api/routers/admin.py:559 - TODO: Implement cleanup tasks
- src/api/routers/admin.py:565 - TODO: Implement job retry logic

**Must-preserve**
- Admin endpoints restricted to admin role — regression test `test_admin_endpoint_requires_admin_role`

## Infra
- src/api/dependencies.py:147-150 - RateLimitChecker default 60 requests/minute
- src/api/dependencies.py:179-183 - Non-premium users limited to 50 quotes/day
- src/api/dependencies.py:216-218 - Preconfigured `check_api_rate_limit` uses 60 req/min
- src/core/config.py:64-69 - AI timeout 30s, max retries 3, cache TTL 3600s, provider rate limits (OpenAI 60, Anthropic 50)
- src/core/config.py:88-93 - Rate limit window 60s with 100 requests; max_file_size 10MB; allowed audio types list
- src/core/config.py:105-106 - Global cache TTL 3600s
- src/core/config.py:123-127 - Feature flags: enable_voice_recognition, enable_ai_psychology, enable_analytics, enable_caching
- src/workers/celery_app.py:14-15 - `REDIS_URL` env fallback to local Redis
- src/workers/celery_app.py:22-23 - Task time limits: 30 min hard, 25 min soft
- src/services/cache/response_cache.py:42-68 - Cache tier TTLs (HOT 300s, WARM 1800s, COLD 3600s; strategy defaults 3600/300/1800 etc.)

**Undocumented rules**
- Non-premium quote quota (50/day)
- API rate limit 60 requests/minute
- Cache TTL hierarchy for tiers and strategies
- Redis fallback to in-memory cache

**Must-preserve**
- Daily quote limit — regression test `test_daily_quote_limit_non_premium`
- API rate limiting — regression test `test_rate_limit_enforced`
- Cache TTL respected — regression test `test_cache_ttl_respected`
- Memory cache acts as Redis fallback — regression test `test_redis_fallback_to_memory`
