# AI Service Documentation

## Overview

The AI Service is a comprehensive, enterprise-ready service for generating high-quality quotes using multiple AI providers. It supports OpenAI GPT-4, Anthropic Claude, and Azure OpenAI with automatic fallback, rate limiting, caching, quality scoring, and cost tracking.

## Features

### 🚀 Core Features
- **Multi-Provider Support**: OpenAI, Anthropic, Azure OpenAI
- **Automatic Fallback**: Seamless provider switching on failures
- **Intelligent Caching**: Redis-based response caching with TTL
- **Rate Limiting**: Per-provider rate limiting with configurable windows
- **Quality Scoring**: Automatic quality assessment of generated quotes
- **Cost Tracking**: Real-time cost calculation and metrics
- **Retry Logic**: Exponential backoff with configurable retry attempts
- **Health Monitoring**: Provider health checks and status monitoring

### 🛡️ Reliability Features
- **Error Handling**: Comprehensive exception handling with detailed logging
- **Circuit Breaker**: Automatic provider isolation on repeated failures
- **Graceful Degradation**: Service continues working even if cache fails
- **Timeout Management**: Configurable timeouts for all operations
- **Async Operations**: Full async/await support for high performance

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Quote Engine  │───▶│   AI Service     │───▶│  Cache Layer    │
│                 │    │                  │    │   (Redis)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │    AI Providers          │
                    ├──────────────────────────┤
                    │ • OpenAI GPT-4          │
                    │ • Anthropic Claude      │
                    │ • Azure OpenAI         │
                    └──────────────────────────┘
```

## Usage

### Basic Usage

```python
from src.services.ai.ai_service import generate_motivational_quote, AIRequest, QuoteCategory

# Simple quote generation
response = await generate_motivational_quote(
    prompt="Success in business",
    context="Entrepreneurship and leadership",
    user_id="user123"
)
print(response.text)
print(f"Quality Score: {response.quality_score}")
print(f"Cost: ${response.cost:.4f}")
```

### Advanced Usage

```python
from src.services.ai.ai_service import AIService, AIRequest, QuoteCategory, AIProvider

# Initialize service
service = AIService()

# Custom request with specific parameters
request = AIRequest(
    prompt="Generate an inspirational quote about perseverance",
    context="Overcoming challenges in professional life",
    category=QuoteCategory.INSPIRATIONAL,
    tone="uplifting",
    max_tokens=200,
    temperature=0.8,
    user_id="user456"
)

# Generate with specific provider preference
response = await service.generate_quote(
    request, 
    preferred_provider=AIProvider.ANTHROPIC
)

# Generate multiple variations
variations = await service.generate_multiple_quotes(request, count=3)
for i, variation in enumerate(variations, 1):
    print(f"Variation {i}: {variation.text}")
    print(f"  Quality: {variation.quality_score:.2f}")
    print(f"  Provider: {variation.provider.value}")
```

### Health Monitoring

```python
# Check provider health
health_status = await service.health_check()
for provider, status in health_status.items():
    print(f"{provider}: {status['status']} ({status['response_time']:.2f}s)")

# Get detailed metrics
metrics = await service.get_metrics()
for provider, provider_metrics in metrics.items():
    print(f"{provider} Metrics:")
    print(f"  Requests: {provider_metrics.requests_count}")
    print(f"  Success Rate: {provider_metrics.success_rate:.2%}")
    print(f"  Total Cost: ${provider_metrics.total_cost:.4f}")
    print(f"  Avg Response Time: {provider_metrics.average_response_time:.2f}s")
```

## Configuration

### Environment Variables

```bash
# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Rate Limiting (requests per minute)
AI_OPENAI_RATE_LIMIT=60
AI_ANTHROPIC_RATE_LIMIT=50
AI_AZURE_RATE_LIMIT=40

# Timeout Settings (seconds)
AI_REQUEST_TIMEOUT=30
AI_CACHE_TTL=3600
```

### Settings Class

```python
from src.core.config import get_settings

settings = get_settings()

# AI Provider Settings
print(f"OpenAI Configured: {bool(settings.OPENAI_API_KEY)}")
print(f"Cache TTL: {settings.AI_CACHE_TTL} seconds")
print(f"Request Timeout: {settings.AI_REQUEST_TIMEOUT} seconds")
```

## API Reference

### Classes

#### AIRequest
```python
@dataclass
class AIRequest:
    prompt: str                    # Main prompt for quote generation
    context: Optional[str] = None  # Additional context
    category: Optional[QuoteCategory] = None
    tone: Optional[str] = None     # e.g., "inspiring", "professional"
    max_tokens: int = 250          # Maximum response length
    temperature: float = 0.7       # Creativity level (0.0-1.0)
    user_id: Optional[str] = None  # For tracking and personalization
```

#### AIResponse
```python
@dataclass
class AIResponse:
    text: str                      # Generated quote
    provider: AIProvider           # Provider used
    model: str                     # AI model used
    tokens_used: int              # Token consumption
    cost: float                   # Cost in USD
    quality_score: float          # Quality score (0.0-1.0)
    response_time: float          # Response time in seconds
    timestamp: datetime           # When generated
    request_id: str               # Unique request identifier
    cached: bool = False          # Whether from cache
```

### Methods

#### AIService.generate_quote()
```python
async def generate_quote(
    self,
    request: AIRequest,
    preferred_provider: Optional[AIProvider] = None,
    use_cache: bool = True
) -> AIResponse:
    """Generate a single quote with automatic fallback."""
```

#### AIService.generate_multiple_quotes()
```python
async def generate_multiple_quotes(
    self,
    request: AIRequest,
    count: int = 3,
    preferred_provider: Optional[AIProvider] = None
) -> List[AIResponse]:
    """Generate multiple quote variations, sorted by quality."""
```

#### AIService.health_check()
```python
async def health_check(self) -> Dict[str, Dict[str, Any]]:
    """Check health status of all providers."""
```

### Convenience Functions

#### generate_motivational_quote()
```python
async def generate_motivational_quote(
    prompt: str,
    context: Optional[str] = None,
    user_id: Optional[str] = None
) -> AIResponse:
    """Generate a motivational quote with preset parameters."""
```

#### generate_professional_quote()
```python
async def generate_professional_quote(
    prompt: str,
    context: Optional[str] = None,
    user_id: Optional[str] = None
) -> AIResponse:
    """Generate a professional quote with preset parameters."""
```

## Quality Scoring

The AI service includes an intelligent quality scoring system that evaluates quotes based on:

1. **Length Appropriateness** (20% weight)
   - Optimal length: 50-200 characters
   - Penalizes very short or very long quotes

2. **Content Quality** (40% weight)
   - Checks for meaningful content
   - Avoids generic or empty responses
   - Ensures proper capitalization and punctuation

3. **Context Relevance** (25% weight)
   - Measures relevance to provided context
   - Uses keyword matching and semantic similarity

4. **Category Alignment** (15% weight)
   - Ensures quote matches requested category
   - Uses category-specific keywords

### Quality Score Interpretation

- **0.8 - 1.0**: Excellent quality
- **0.6 - 0.8**: Good quality
- **0.4 - 0.6**: Acceptable quality
- **0.0 - 0.4**: Poor quality (may trigger regeneration)

## Rate Limiting

Each provider has independent rate limiting:

- **Sliding Window**: Configurable time window
- **Per-Provider Limits**: Individual limits for each service
- **Automatic Fallback**: Switches to available providers
- **Graceful Recovery**: Automatically resumes when limits reset

### Default Limits
- OpenAI: 60 requests/minute
- Anthropic: 50 requests/minute  
- Azure OpenAI: 40 requests/minute

## Caching Strategy

The service implements intelligent caching to reduce costs and improve performance:

### Cache Key Generation
- Based on request parameters (prompt, context, category, etc.)
- MD5 hash for consistent, compact keys
- Cache namespace: `ai_service:`

### Cache Behavior
- **TTL**: 1 hour default (configurable)
- **Automatic Invalidation**: Based on content changes
- **Cache Miss Handling**: Transparent fallback to API
- **Error Resilience**: Service works even if cache fails

### Cache Statistics
- Hit/miss ratios tracked per provider
- Cost savings calculations
- Performance impact metrics

## Cost Tracking

Real-time cost tracking with detailed breakdown:

### Cost Calculation
- **Token-based pricing** for all providers
- **Real-time rates** updated automatically  
- **Per-request tracking** with detailed logging
- **Aggregated metrics** for analysis

### Cost Optimization Features
- **Cache utilization** to reduce API calls
- **Provider cost comparison** for optimal selection
- **Budget alerts** and usage monitoring
- **Cost prediction** based on usage patterns

## Error Handling

Comprehensive error handling with specific exception types:

### Exception Hierarchy
```python
AIServiceError                    # Base exception
├── RateLimitError               # Rate limit exceeded
├── QuotaExceededError           # Provider quota exceeded
├── InvalidRequestError          # Malformed request
├── ProviderUnavailableError     # Provider service down
└── QualityThresholdError        # Generated content below threshold
```

### Error Recovery Strategies
1. **Automatic Retry**: Exponential backoff for transient errors
2. **Provider Fallback**: Switch to alternative providers
3. **Cache Fallback**: Return cached results if available
4. **Graceful Degradation**: Simplified responses when needed

## Performance Optimization

### Async Architecture
- Full async/await support
- Concurrent provider requests for health checks
- Non-blocking cache operations
- Efficient connection pooling

### Performance Metrics
- Response time tracking per provider
- Token usage optimization
- Cache hit rate monitoring
- Provider selection optimization

## Testing

### Unit Tests
```bash
# Run unit tests
pytest tests/unit/test_ai_service.py -v

# Run with coverage
pytest tests/unit/test_ai_service.py --cov=src.services.ai.ai_service
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/test_ai_service_integration.py -v

# Test specific scenarios
pytest tests/integration/test_ai_service_integration.py::TestAIServiceIntegration::test_end_to_end_quote_generation -v
```

### Performance Tests
```bash
# Run performance benchmarks
pytest tests/performance/test_ai_service_performance.py -v
```

## Monitoring and Observability

### Logging
- Structured logging with `structlog`
- Request/response logging with sanitized data
- Performance metrics logging
- Error tracking with full context

### Metrics
- Prometheus-compatible metrics
- Provider performance metrics
- Cost and usage tracking
- Quality score distributions

### Health Checks
- Provider availability monitoring
- Response time tracking
- Error rate monitoring
- Cache health status

## Security Considerations

### API Key Management
- Environment variable storage
- No hardcoded credentials
- Secure key rotation support
- Access logging

### Data Privacy
- Request sanitization
- No sensitive data caching
- User ID anonymization
- GDPR compliance features

### Network Security
- TLS/SSL for all API communications
- Request timeout protection
- Rate limiting protection
- Input validation

## Deployment

### Docker Configuration
```dockerfile
# Install AI service dependencies
RUN pip install -r requirements/ai_service.txt

# Set environment variables
ENV OPENAI_API_KEY=""
ENV ANTHROPIC_API_KEY=""
ENV AZURE_OPENAI_API_KEY=""
ENV REDIS_URL="redis://redis:6379/0"
```

### Kubernetes Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-service-config
data:
  REDIS_URL: "redis://redis-service:6379/0"
  AI_REQUEST_TIMEOUT: "30"
  AI_CACHE_TTL: "3600"
---
apiVersion: v1
kind: Secret
metadata:
  name: ai-service-secrets
type: Opaque
stringData:
  OPENAI_API_KEY: "your-openai-key"
  ANTHROPIC_API_KEY: "your-anthropic-key"
  AZURE_OPENAI_API_KEY: "your-azure-key"
```

## Troubleshooting

### Common Issues

#### Provider Connection Issues
```python
# Check provider health
health = await service.health_check()
if health['openai']['status'] != 'healthy':
    print(f"OpenAI Issue: {health['openai']['error']}")
```

#### Rate Limiting
```python
# Check rate limit status
try:
    response = await service.generate_quote(request)
except RateLimitError as e:
    print(f"Rate limited: {e.provider} - Retry after {e.retry_after}s")
```

#### Cache Issues
```python
# Test cache connectivity
try:
    await service.cache.ping()
    print("Cache is healthy")
except Exception as e:
    print(f"Cache issue: {e}")
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
service = AIService(debug=True)
```

## Roadmap

### Upcoming Features
- **Model Selection**: Dynamic model selection based on request complexity
- **Custom Models**: Support for fine-tuned models
- **Batch Processing**: Efficient batch quote generation
- **A/B Testing**: Built-in A/B testing for different providers
- **Analytics Dashboard**: Web interface for metrics and monitoring
- **Auto-scaling**: Dynamic rate limit adjustment
- **Cost Optimization**: ML-based provider selection for cost efficiency

### Performance Improvements
- **Connection Pooling**: Optimized HTTP connection management
- **Predictive Caching**: ML-based cache pre-population
- **Load Balancing**: Intelligent request distribution
- **Edge Caching**: Geographic content distribution

## Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

### Code Standards
- Type hints for all functions
- Comprehensive docstrings
- 90% test coverage minimum
- Performance benchmarks for new features

## License

This AI Service is part of the Quote Master Pro application and is subject to the project's licensing terms.

---

*For support and questions, please refer to the project's issue tracker or contact the development team.*
