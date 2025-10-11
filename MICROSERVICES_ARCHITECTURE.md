# Microservices Architecture

## Overview

This document describes the microservices architecture extraction from the monolithic application. The system has been decomposed into independent, scalable services that communicate through a central API Gateway.

## Architecture

```
┌─────────────────┐
│   API Gateway   │ (8000)
│   - Routing     │
│   - Auth        │
│   - API Keys    │
└────────┬────────┘
         │
    ┌────┴──────┬──────────┬──────────┐
    │            │          │          │
    ▼            ▼          ▼          ▼
┌─────────┐ ┌────────────┐ ┌──────────┐ ┌─────────────┐
│  Auth   │ │Notification│ │Analytics │ │  (Future)   │
│Service  │ │  Service   │ │ Service  │ │  Services   │
│ (8001)  │ │   (8002)   │ │  (8003)  │ │             │
└────┬────┘ └─────┬──────┘ └─────┬────┘ └─────────────┘
     │            │              │
     └────────────┴──────────────┘
          Service Discovery
          & Health Checks
```

## Services

### 1. Authentication Service (Port 8001)

**Responsibility**: User authentication, session management, and token generation.

**Key Endpoints**:
- `POST /register` - Register new user
- `POST /login` - Authenticate user and get token
- `GET /me` - Get current user profile
- `PUT /me` - Update user profile
- `POST /change-password` - Change user password
- `POST /logout` - Logout user
- `POST /health` - Health check

**Features**:
- JWT token generation and validation
- Session management
- MFA support (extensible)
- Audit logging
- Password hashing

**Dependencies**: None (independent)

### 2. Notification Service (Port 8002)

**Responsibility**: Email, SMS, and push notifications.

**Key Endpoints**:
- `POST /send` - Send notification to user
- `POST /send-batch` - Send notifications to multiple users
- `GET /user/{user_id}` - Get user notifications
- `GET /notification/{notification_id}` - Get specific notification
- `POST /health` - Health check

**Features**:
- Multi-channel notifications (email, SMS, push)
- Batch notification support
- Notification tracking and history
- Retry logic for failed notifications

**Dependencies**: None (independent)

### 3. Analytics Service (Port 8003)

**Responsibility**: Financial analytics, metrics, and insights.

**Key Endpoints**:
- `POST /query` - Query analytics data
- `POST /health` - Health check
- `GET /health/detailed` - Detailed health status

**Supported Metrics**:
- `cash_flow` - Income vs expenses analysis
- `spending_trends` - Category-wise spending trends
- `health_score` - Financial health score
- `anomalies` - Anomaly detection

**Features**:
- Real-time metric calculations
- Caching for performance
- Anomaly detection
- Trend analysis
- Financial insights

**Dependencies**: None (independent)

### 4. API Gateway (Port 8000)

**Responsibility**: Request routing, authentication, and service discovery.

**Key Features**:
- Request routing to appropriate microservices
- API key validation
- Correlation ID propagation
- Service health aggregation
- Load balancing (basic round-robin)
- Backward compatibility with monolith API

**Health Endpoints**:
- `GET /health` - Gateway and all services health
- `GET /registry` - Service registry status

## Core Infrastructure

### Service Registry

**File**: `services/core/service_registry.py`

In-memory service discovery registry. Each service registers itself on startup.

```python
registry.register(
    service_name="auth-service",
    instance_id="auth-1",
    host="localhost",
    port=8001,
    health_check_url="/health",
    api_key="auth-key-123"
)
```

**Features**:
- Service registration and deregistration
- Health tracking
- Load balancing
- Stale instance cleanup

### Correlation IDs

**File**: `services/core/correlation_id.py`

Tracks requests across service boundaries for distributed tracing.

- Generated automatically on API Gateway entry
- Passed through `X-Correlation-ID` header
- Included in all logs for correlation

```python
with CorrelationContext("service-name", "correlation-id-123"):
    # Service code
    logger.info("Request processed")  # Includes correlation ID in logs
```

### Health Checks

**File**: `services/core/health_check.py`

Comprehensive health checking for services.

```python
health_checker = ServiceHealthChecker("auth-service")
health_checker.register_check(DatabaseHealthCheck(db))
health_checker.register_callable_check("redis", check_redis)
```

**Built-in Checks**:
- Database connectivity
- Memory usage
- Disk usage
- External service availability

### Service-to-Service Communication

**File**: `services/core/api_client.py`

Resilient HTTP client with retry logic and service discovery.

**Features**:
- Automatic service discovery
- Exponential backoff retry
- Request correlation propagation
- Health monitoring
- Timeout handling

```python
client = await client_factory.get_client("auth-service")
result = await client.post("/register", json=user_data)
```

## API Key Authentication

### Service-to-Service

Each service has a unique API key for internal communication:
- Auth Service: `AUTH_SERVICE_API_KEY`
- Notification Service: `NOTIFICATION_SERVICE_API_KEY`
- Analytics Service: `ANALYTICS_SERVICE_API_KEY`

API keys are validated in the API Gateway and passed through `X-API-Key` header.

### Client Authentication

External clients use API keys via `X-API-Key` header:

```bash
curl -H "X-API-Key: client-key-1" http://localhost:8000/auth/login
```

## Deployment

### Docker Compose

Start all services with:

```bash
docker-compose -f docker-compose.services.yml up
```

### Individual Service Build

```bash
# Build auth service
docker build \
  -t auth-service:latest \
  -f services/Dockerfile \
  --build-arg SERVICE_NAME=auth_service \
  .

# Run service
docker run -p 8001:8001 \
  -e SERVICE_HOST=0.0.0.0 \
  -e SERVICE_PORT=8001 \
  -e AUTH_SERVICE_API_KEY=auth-key-dev \
  auth-service:latest
```

### Environment Variables

**Gateway**:
- `GATEWAY_HOST`: Gateway host (default: localhost)
- `GATEWAY_PORT`: Gateway port (default: 8000)
- `GATEWAY_API_KEY`: Gateway API key
- `ALLOWED_API_KEYS`: Comma-separated list of allowed client API keys

**Auth Service**:
- `SERVICE_HOST`: Service host (default: localhost)
- `SERVICE_PORT`: Service port (default: 8001)
- `JWT_SECRET_KEY`: JWT signing secret

**Common**:
- `LOG_LEVEL`: Logging level (default: INFO)
- `SERVICE_INSTANCE_ID`: Unique instance identifier

## Request Flow

### User Registration Flow

```
Client Request
    │
    ▼
API Gateway (/auth/register)
    │
    ├─ Validate API Key
    ├─ Generate Correlation ID
    │
    ▼
Auth Service (/register)
    │
    ├─ Validate input
    ├─ Hash password
    ├─ Store user
    │
    ▼
Return response
```

### Cross-Service Communication

```
Auth Service (needs to send notification)
    │
    ├─ Get service client from factory
    ├─ Client discovery: "notification-service"
    │
    ▼
Service Registry
    │ Returns instance of notification-service
    │
    ▼
HTTP Client
    │
    ├─ Add X-API-Key header
    ├─ Add X-Correlation-ID header
    ├─ Retry with exponential backoff
    │
    ▼
Notification Service (/send)
    │
    ├─ Validate API Key
    ├─ Validate Correlation ID
    ├─ Process request
    │
    ▼
Return response
```

## Resilience Patterns

### Retry Logic

Automatic retry with exponential backoff for transient failures:

```python
RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    retry_on_status_codes=[408, 429, 500, 502, 503, 504]
)
```

### Circuit Breaker (Future)

Services that fail repeatedly are marked as unhealthy and removed from rotation.

### Health Checks

- Services register health endpoints
- API Gateway periodically checks service health
- Unhealthy services are isolated

## Backward Compatibility

The API Gateway maintains backward compatibility with the original monolith API:

```
Original Endpoint          →  New Endpoint
/api/auth/register         →  Gateway → Auth Service
/api/auth/login            →  Gateway → Auth Service
/api/notifications/send    →  Gateway → Notification Service
/api/analytics/query       →  Gateway → Analytics Service
```

Existing clients continue to work without modification.

## Monitoring & Logging

### Structured Logging

All logs include service context:

```json
{
  "message": "User registered",
  "service": "auth-service",
  "correlation_id": "req-12345",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "user_id": 42
}
```

### Health Monitoring

```bash
# Check gateway health
curl http://localhost:8000/health

# Check service registry
curl -H "X-API-Key: gateway-key-dev" http://localhost:8000/registry

# Check individual service
curl http://localhost:8001/health
```

## Scaling

### Horizontal Scaling

Add more instances of a service:

```bash
# Start second auth service instance
docker run -p 8011:8001 \
  -e SERVICE_HOST=0.0.0.0 \
  -e SERVICE_PORT=8001 \
  -e SERVICE_INSTANCE_ID=auth-2 \
  auth-service:latest
```

The service registry will automatically discover and load balance between instances.

### Vertical Scaling

Adjust resources in docker-compose.yml:

```yaml
auth-service:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

## Testing

Run integration tests:

```bash
pytest services/tests/test_integration.py -v
```

Test failure scenarios:

```bash
# Stop a service and observe failover
docker stop auth-service

# Make requests to gateway
curl -H "X-API-Key: client-key-1" http://localhost:8000/auth/me
# Should get service unavailable error
```

## Migration Path

### Phase 1: Extract Core Services (Current)
- Authentication Service ✓
- Notification Service ✓
- Analytics Service ✓

### Phase 2: Extract Business Logic
- Payment Service
- Transaction Service
- Account Service

### Phase 3: Deprecate Monolith
- Migrate remaining endpoints
- Sunset monolithic API

### Phase 4: Full Microservices
- Independent deployments
- Team ownership
- True scaling and resilience

## Rollback Procedures

### Quick Rollback

If issues with new services, route traffic back to monolith:

1. Update API Gateway routes to point to monolith endpoints
2. Stop microservices
3. Keep monolith running alongside

```yaml
# Gateway configuration to use monolith
MONOLITH_HOST=original-app.example.com
MONOLITH_PORT=8000
ROUTE_TO_MONOLITH=true
```

### Gradual Rollback

Use percentage-based routing:

```python
# Route 10% to new service, 90% to monolith
if random.random() < 0.1:
    return await new_service_client.post(...)
else:
    return await monolith_client.post(...)
```

## Troubleshooting

### Service Not Registering

1. Check service logs: `docker logs auth-service`
2. Verify network connectivity: `docker network inspect microservices`
3. Check API key configuration

### High Latency

1. Check service health: `GET /health`
2. Review retry counts in logs
3. Check network latency: `docker exec auth-service ping notification-service`

### Correlation ID Not Found

1. Check API Gateway is adding header
2. Verify downstream services propagate header
3. Check structured logging configuration

## Future Enhancements

1. **Service Mesh**: Implement Istio or Linkerd for advanced routing
2. **Event-Driven**: Add message queue for async communication
3. **API Versioning**: Support multiple API versions
4. **Rate Limiting**: Per-service and per-client limits
5. **Caching Layer**: Add Redis for distributed caching
6. **API Documentation**: OpenAPI/Swagger for each service
7. **Authentication Enhancement**: OAuth2, SAML support
8. **Distributed Tracing**: Jaeger or Zipkin integration

## References

- [12 Factor App](https://12factor.net/)
- [Microservices Patterns](https://microservices.io/patterns/index.html)
- [API Gateway Pattern](https://microservices.io/patterns/apigateway.html)
- [Service Discovery](https://microservices.io/patterns/service-discovery.html)
