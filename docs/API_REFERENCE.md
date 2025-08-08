# Quote Master Pro - API Reference

## 📋 Table of Contents

- [🚀 Getting Started](#-getting-started)
- [🔐 Authentication](#-authentication)
- [📝 Quote Generation](#-quote-generation)
- [🎤 Voice Processing](#-voice-processing)
- [👤 User Management](#-user-management)
- [📊 Analytics](#-analytics)
- [⚙️ Administration](#️-administration)
- [📈 Monitoring](#-monitoring)
- [🔧 Error Handling](#-error-handling)
- [📊 Rate Limiting](#-rate-limiting)

---

## 🚀 Getting Started

### **Base URL**

```
Development: http://localhost:8000
Production:  https://api.quotemasterpro.com
```

### **Interactive Documentation**

- **Swagger UI**: `{BASE_URL}/docs`
- **ReDoc**: `{BASE_URL}/redoc`
- **OpenAPI Spec**: `{BASE_URL}/openapi.json`

### **API Versioning**

All API endpoints are versioned and prefixed with `/api/v1/`.

### **Response Format**

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid-here"
}
```

### **Error Response Format**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": ["Field is required"]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid-here"
}
```

---

## 🔐 Authentication

### **Register User**

```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "is_verified": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### **Login**

```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "username": "johndoe",
      "role": "user"
    }
  }
}
```

### **Refresh Token**

```http
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "jwt-refresh-token"
}
```

### **Logout**

```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

### **Password Reset Request**

```http
POST /api/v1/auth/password/reset-request
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

### **Password Reset Confirm**

```http
POST /api/v1/auth/password/reset-confirm
```

**Request Body:**
```json
{
  "token": "reset-token",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

---

## 📝 Quote Generation

### **Generate Quote (Enhanced)**

```http
POST /api/v1/quotes/generate/enhanced
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "prompt": "inspiration for overcoming challenges",
  "style": "motivational",
  "tone": "positive",
  "length": "medium",
  "author_style": "Maya Angelou",
  "context": "professional development",
  "ai_model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 150,
  "include_psychology": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "text": "The strongest people are not those who show strength in front of us, but those who win battles we know nothing about.",
    "author": "Maya Angelou Style",
    "style": "motivational",
    "tone": "positive",
    "quality_score": 0.92,
    "sentiment_score": 0.85,
    "psychological_profile": {
      "emotional_tone": "hopeful",
      "complexity_score": 0.75,
      "inspiration_level": 0.88
    },
    "ai_model": "gpt-4",
    "generation_time_ms": 1250,
    "cost_estimate": 0.003,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### **Streaming Quote Generation**

```http
POST /api/v1/quotes/generate/stream
Authorization: Bearer {access_token}
Content-Type: application/json
```

Returns Server-Sent Events (SSE) stream:

```
data: {"type": "processing", "message": "Analyzing prompt..."}

data: {"type": "generating", "message": "Generating quote..."}

data: {"type": "complete", "quote": {...}}
```

### **AI Service Health Check**

```http
GET /api/v1/quotes/ai-service/health
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "service_status": "healthy",
    "providers": {
      "openai": {
        "status": "healthy",
        "response_time_ms": 450,
        "success_rate": 0.98,
        "circuit_breaker_state": "closed"
      },
      "anthropic": {
        "status": "healthy",
        "response_time_ms": 520,
        "success_rate": 0.96,
        "circuit_breaker_state": "closed"
      }
    },
    "total_requests_today": 1250,
    "average_response_time": 485
  }
}
```

### **Reset Circuit Breaker**

```http
POST /api/v1/quotes/ai-service/circuit-breaker/reset/{provider}
Authorization: Bearer {access_token}
```

**Path Parameters:**
- `provider`: `openai`, `anthropic`, or `azure`

---

## 🎤 Voice Processing

### **Transcribe Audio**

```http
POST /api/v1/voice/transcribe
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Form Data:**
- `audio_file`: Audio file (wav, mp3, m4a, flac)
- `language`: Optional language code (e.g., "en", "es", "fr")
- `model`: Optional Whisper model ("base", "small", "medium", "large")

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "transcription": "I need some inspiration to overcome the challenges I'm facing at work.",
    "language": "en",
    "confidence": 0.95,
    "duration_seconds": 8.5,
    "processing_time_ms": 2100,
    "segments": [
      {
        "start": 0.0,
        "end": 8.5,
        "text": "I need some inspiration to overcome the challenges I'm facing at work."
      }
    ]
  }
}
```

### **Generate Quote from Voice**

```http
POST /api/v1/voice/quote-from-voice
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Form Data:**
- `audio_file`: Audio file
- `style`: Quote style (optional)
- `tone`: Quote tone (optional)
- `include_psychology`: Boolean (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "transcription": "I need some inspiration to overcome challenges",
    "quote": {
      "id": "uuid-here",
      "text": "Every challenge is an opportunity to grow stronger and wiser.",
      "quality_score": 0.89,
      "style": "inspirational",
      "psychological_profile": {
        "motivation_level": 0.92,
        "resilience_factor": 0.88
      }
    },
    "processing_time_ms": 3200
  }
}
```

### **List Voice Recordings**

```http
GET /api/v1/voice/recordings
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `limit`: Number of records (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status ("pending", "completed", "failed")

**Response:**
```json
{
  "success": true,
  "data": {
    "recordings": [
      {
        "id": "uuid-here",
        "filename": "recording_2024-01-15.wav",
        "duration_seconds": 8.5,
        "status": "completed",
        "transcription": "...",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### **Delete Voice Recording**

```http
DELETE /api/v1/voice/recordings/{recording_id}
Authorization: Bearer {access_token}
```

---

## 👤 User Management

### **Get Current User**

```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "bio": "Quote enthusiast and writer",
    "role": "user",
    "is_verified": true,
    "is_active": true,
    "subscription_tier": "premium",
    "total_quotes_generated": 156,
    "total_voice_requests": 23,
    "created_at": "2024-01-10T15:30:00Z",
    "last_login_at": "2024-01-15T09:15:00Z"
  }
}
```

### **Update User Profile**

```http
PUT /api/v1/users/profile
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "full_name": "John Smith",
  "bio": "Writer and motivational speaker",
  "timezone": "America/New_York",
  "language": "en"
}
```

### **Change Password**

```http
POST /api/v1/auth/password/change
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "current_password": "CurrentPass123!",
  "new_password": "NewSecurePass123!",
  "confirm_password": "NewSecurePass123!"
}
```

### **Get User Statistics**

```http
GET /api/v1/users/stats
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_quotes": 156,
    "total_favorites": 23,
    "total_voice_recordings": 12,
    "quotes_this_month": 28,
    "average_quotes_per_day": 1.2,
    "most_used_style": "inspirational",
    "join_date": "2024-01-10T15:30:00Z",
    "days_active": 15
  }
}
```

---

## 📊 Analytics

### **User Dashboard Data**

```http
GET /api/v1/analytics/dashboard
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `period`: Time period ("day", "week", "month", "year")
- `timezone`: User timezone (default: UTC)

**Response:**
```json
{
  "success": true,
  "data": {
    "period": "month",
    "summary": {
      "quotes_generated": 28,
      "voice_recordings": 5,
      "favorites_added": 12,
      "shares": 8
    },
    "daily_activity": [
      {
        "date": "2024-01-15",
        "quotes_generated": 3,
        "voice_recordings": 1
      }
    ],
    "style_breakdown": {
      "inspirational": 12,
      "motivational": 8,
      "philosophical": 5,
      "humorous": 3
    },
    "mood_trends": {
      "positive": 0.75,
      "neutral": 0.20,
      "negative": 0.05
    }
  }
}
```

### **Quote Analytics**

```http
GET /api/v1/analytics/quotes
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `quote_id`: Specific quote ID (optional)
- `period`: Time period for aggregation
- `group_by`: Grouping dimension ("style", "tone", "ai_model")

### **Usage Analytics**

```http
GET /api/v1/analytics/usage
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_month": {
      "api_calls": 156,
      "ai_tokens_used": 45000,
      "voice_minutes": 23.5,
      "storage_mb": 12.3
    },
    "usage_limits": {
      "api_calls_limit": 1000,
      "ai_tokens_limit": 100000,
      "voice_minutes_limit": 60,
      "storage_mb_limit": 100
    },
    "cost_estimate": {
      "current_month": 2.45,
      "projected_month": 3.20
    }
  }
}
```

---

## ⚙️ Administration

> **Note**: Admin endpoints require `admin` role.

### **Get System Health**

```http
GET /api/v1/admin/health
Authorization: Bearer {admin_access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system_status": "healthy",
    "components": {
      "database": {
        "status": "healthy",
        "response_time_ms": 15,
        "connections_active": 8,
        "connections_idle": 12
      },
      "redis": {
        "status": "healthy",
        "memory_usage": "45.2MB",
        "hit_rate": 0.89
      },
      "ai_services": {
        "status": "healthy",
        "providers_available": 2,
        "average_response_time": 485
      }
    },
    "uptime_seconds": 86400,
    "version": "1.0.0"
  }
}
```

### **List All Users**

```http
GET /api/v1/admin/users
Authorization: Bearer {admin_access_token}
```

**Query Parameters:**
- `limit`, `offset`: Pagination
- `role`: Filter by role
- `status`: Filter by account status
- `search`: Search by email/username

### **User Management Actions**

```http
POST /api/v1/admin/users/{user_id}/actions
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "action": "deactivate",  // "activate", "deactivate", "verify", "upgrade_role"
  "reason": "Violation of terms of service"
}
```

---

## 📈 Monitoring

### **System Metrics**

```http
GET /api/v1/monitoring/metrics
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-15T10:30:00Z",
    "system": {
      "cpu_usage": 0.35,
      "memory_usage": 0.68,
      "disk_usage": 0.42
    },
    "application": {
      "requests_per_second": 125.5,
      "average_response_time": 245,
      "error_rate": 0.008
    },
    "business": {
      "quotes_generated_today": 1250,
      "active_users": 85,
      "revenue_today": 450.75
    }
  }
}
```

### **Health Check**

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1705316400.123,
  "checks": {
    "database": true,
    "ai_service": true,
    "overall": true
  }
}
```

---

## 🔧 Error Handling

### **HTTP Status Codes**

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### **Error Codes**

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTHENTICATION_ERROR` | Invalid credentials |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `AI_SERVICE_ERROR` | AI provider error |
| `VOICE_PROCESSING_ERROR` | Audio processing failed |
| `DATABASE_ERROR` | Database operation failed |
| `NETWORK_ERROR` | External service unavailable |

### **Example Error Response**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "prompt": ["Field is required"],
      "max_tokens": ["Must be between 10 and 4000"]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_1234567890"
}
```

---

## 📊 Rate Limiting

### **Rate Limit Headers**

All responses include rate limit headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705316400
X-RateLimit-Window: 3600
```

### **Rate Limits by Tier**

| Tier | API Calls/Hour | AI Requests/Hour | Voice Minutes/Day |
|------|----------------|------------------|-------------------|
| **Free** | 100 | 20 | 5 |
| **Basic** | 1,000 | 200 | 30 |
| **Premium** | 10,000 | 2,000 | 120 |
| **Enterprise** | Unlimited | Unlimited | Unlimited |

### **Rate Limit Exceeded Response**

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": 3600,
      "reset_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

---

## 🔄 Webhooks (Coming Soon)

### **Available Events**

- `quote.generated` - New quote generated
- `user.registered` - New user registration
- `voice.transcribed` - Voice transcription complete
- `payment.completed` - Subscription payment processed

### **Webhook Configuration**

```http
POST /api/v1/webhooks
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/quotes",
  "events": ["quote.generated", "voice.transcribed"],
  "secret": "webhook-secret-key"
}
```

---

## 📱 SDKs and Libraries

### **Official SDKs**

- **Python**: `pip install quotemasterpro-python`
- **JavaScript**: `npm install quotemasterpro-js`
- **TypeScript**: Built-in TypeScript support

### **Python SDK Example**

```python
from quotemasterpro import QuoteMasterClient

client = QuoteMasterClient(api_key="your-api-key")

quote = client.quotes.generate(
    prompt="inspiration for success",
    style="motivational"
)

print(quote.text)
```

### **JavaScript SDK Example**

```javascript
import { QuoteMasterClient } from 'quotemasterpro-js';

const client = new QuoteMasterClient({ apiKey: 'your-api-key' });

const quote = await client.quotes.generate({
  prompt: 'inspiration for success',
  style: 'motivational'
});

console.log(quote.text);
```

---

This API reference provides comprehensive documentation for all endpoints. For interactive testing, use the Swagger UI at `/docs` or ReDoc at `/redoc`.
