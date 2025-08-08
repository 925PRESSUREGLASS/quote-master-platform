# Hotspots – Last 180 Days

## Summary
- **Reverts:** None detected.
- **Hotfixes:** None detected.
- **Large diffs identified:**
  - AI service infrastructure
  - Unified quote generator
  - Voice handling stack
  - Authentication and security

## Details

### AI Service Infrastructure
- **Commit:** `079c303` – Phase 1 Complete: Enhanced AI Service Infrastructure
- **Files:** `src/services/ai/enhanced_ai_service.py`, `src/services/ai/monitoring/circuit_breaker.py`, `src/services/ai/monitoring/smart_routing.py`, `src/services/ai/monitoring/tracing.py`
- **Reason:** Introduced multi-provider AI routing, circuit breakers, telemetry and tracing.
- **Root cause:** Initial AI layer lacked resilience and observability.
- **Real fix:** Added smart routing, circuit breakers, and comprehensive tracing.

### Unified Quote Generator
- **Commit:** `2327b6b` – Transform repository to window & pressure cleaning services
- **Files:** `src/services/quote/unified_generator.py`, `src/services/quote/unified_generator_backup.py`
- **Reason:** Full rewrite to support service-based quotes instead of inspirational quotes.
- **Root cause:** Business pivot required new pricing logic and service orchestration.
- **Real fix:** Implemented unified service generator with dynamic pricing, property assessment and caching.

### Unified Generator Cleanup
- **Commit:** `30c9aa1` – Comprehensive Cleanup & Refactoring
- **Files:** `src/services/quote/unified_generator.py`
- **Reason:** Remove technical debt and split monolithic logic into helpers.
- **Root cause:** Previous generator grew too large and hard to maintain.
- **Real fix:** Extracted helper methods and optimized imports for maintainability.

### Voice Handling Stack
- **Commit:** `6593113` – Add complete Quote Master Pro project files
- **Files:** `src/api/routers/voice.py`, `src/services/voice/processor.py`, `src/services/voice/recognizer.py`, `src/services/voice/whisper.py`
- **Reason:** Introduced voice recording, processing and transcription pipeline.
- **Root cause:** Platform initially lacked voice features.
- **Real fix:** Added processor, recognizer and Whisper-based transcription modules.

### Authentication & Security
- **Commit:** `6593113` – Add complete Quote Master Pro project files
- **Files:** `src/api/routers/auth.py`, `src/core/security.py`
- **Reason:** Establish JWT authentication and security utilities.
- **Root cause:** No user authentication mechanism existed.
- **Real fix:** Implemented auth endpoints and security helpers for token management.

## "Never Again" Tests
1. **test_ai_service_failover**  
   - **Given** primary AI provider is unavailable  
   - **When** requesting a quote  
   - **Then** service routes to the secondary provider without failure
2. **test_unified_generator_handles_all_services**  
   - **Given** all supported service types  
   - **When** generating quotes  
   - **Then** returns pricing for each type
3. **test_voice_upload_and_transcription**  
   - **Given** a valid audio sample  
   - **When** posted to the voice endpoint  
   - **Then** transcription is stored and retrievable
4. **test_auth_token_revocation**  
   - **Given** a revoked JWT  
   - **When** accessing a protected route  
   - **Then** request is rejected with 401

