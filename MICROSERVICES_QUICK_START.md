# Microservices Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ (for local development)
- Basic understanding of REST APIs

### Start All Services

```bash
# Navigate to project root
cd /Volumes/T9/TASK-574/model_b

# Start all services with Docker Compose
docker-compose -f docker-compose.services.yml up -d

# Verify services are running
docker-compose -f docker-compose.services.yml ps

# Check gateway health
curl http://localhost:8000/health
```

### Verify Setup

```bash
# Get service registry status
curl -H "X-API-Key: gateway-key-dev" http://localhost:8000/registry

# Expected output shows 3 registered services:
# - auth-service (port 8001)
# - notification-service (port 8002)
# - analytics-service (port 8003)
```

## 📝 Example API Usage

### Authentication Service

```bash
# Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "X-API-Key: client-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0123",
    "currency": "USD",
    "timezone": "America/New_York"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "X-API-Key: client-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'

# Get current user (requires Bearer token from login response)
curl -X GET http://localhost:8000/auth/me \
  -H "X-API-Key: client-key-1" \
  -H "Authorization: Bearer <your-token-here>"
```

### Notification Service

```bash
# Send notification
curl -X POST http://localhost:8000/notifications/send \
  -H "X-API-Key: client-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "notification_type": "email",
    "recipient": "john@example.com",
    "subject": "Test Notification",
    "body": "This is a test notification"
  }'

# Get user notifications
curl -X GET "http://localhost:8000/notifications/user/1?limit=10&offset=0" \
  -H "X-API-Key: client-key-1"
```

### Analytics Service

```bash
# Query analytics
curl -X POST http://localhost:8000/analytics/query \
  -H "X-API-Key: client-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "metric": "cash_flow",
    "period_days": 30
  }'

# Available metrics:
# - cash_flow: Income vs expenses
# - spending_trends: Category spending analysis
# - health_score: Financial health score
# - anomalies: Anomaly detection
```

## 🧪 Run Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest services/tests/test_integration.py -v

# Run specific test class
pytest services/tests/test_integration.py::TestServiceRegistry -v

# Run with coverage
pytest services/tests/test_integration.py --cov=services --cov-report=html
```

## 📊 Monitor Services

### Health Status

```bash
# Gateway health (includes all services)
curl http://localhost:8000/health | jq

# Individual service health
curl http://localhost:8001/health | jq
curl http://localhost:8002/health | jq
curl http://localhost:8003/health | jq
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.services.yml logs -f

# Specific service
docker-compose -f docker-compose.services.yml logs -f auth-service

# Last 50 lines
docker compose -f docker-compose.services.yml logs --tail=50 notification-service
```

## 🔌 Service-to-Service Communication

Services automatically discover and communicate with each other through the service registry:

```python
# Example: Auth service calling Notification service
from services.core.api_client import get_client_factory

async def notify_user_registered(user_id: int, email: str):
    factory = get_client_factory()
    client = await factory.get_client("notification-service")

    result = await client.post("/send", json={
        "user_id": user_id,
        "notification_type": "email",
        "recipient": email,
        "subject": "Welcome",
        "body": "Thanks for registering!"
    })

    return result
```

## 🔐 API Key Management

### Gateway API Keys

Default keys (for development):

```bash
# Gateway key (for internal use)
GATEWAY_API_KEY=gateway-key-dev

# Client keys (for external use)
ALLOWED_API_KEYS=client-key-1,client-key-2
```

### Service API Keys

```bash
# Auth service
AUTH_SERVICE_API_KEY=auth-key-dev

# Notification service
NOTIFICATION_SERVICE_API_KEY=notification-key-dev

# Analytics service
ANALYTICS_SERVICE_API_KEY=analytics-key-dev
```

All requests must include `X-API-Key` header.

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Docker logs
docker-compose -f docker-compose.services.yml logs

# Verify port availability
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :8003

# Clear volumes and restart
docker-compose -f docker-compose.services.yml down -v
docker-compose -f docker-compose.services.yml up
```

### Connection Refused

```bash
# Check if services are running
docker-compose -f docker-compose.services.yml ps

# Check service network
docker network inspect microservices

# Verify service discovery
curl -H "X-API-Key: gateway-key-dev" http://localhost:8000/registry
```

### High Response Times

```bash
# Check service health
curl http://localhost:8000/health | jq '.services'

# Check resource usage
docker stats

# Review logs for errors
docker-compose -f docker-compose.services.yml logs --tail=100 | grep -i error
```

## 📚 Documentation

- **MICROSERVICES_ARCHITECTURE.md** - Detailed architecture documentation
- **MIGRATION_GUIDE.md** - Step-by-step migration instructions
- Service API documentation available at `/docs` when using FastAPI (can be added)

## 🛠️ Development

### Modify a Service

1. Edit service code in `services/service_name/`
2. Restart service: `docker-compose -f docker-compose.services.yml restart auth-service`
3. View logs: `docker-compose -f docker-compose.services.yml logs -f auth-service`

### Add New Endpoint

```python
# In services/auth_service/app.py
@app.get("/custom-endpoint")
async def custom_endpoint(request: Request):
    """New custom endpoint."""
    logger.info("Custom endpoint called")
    return {"message": "Success"}
```

### Build Custom Docker Image

```bash
# Build specific service
docker build \
  -t auth-service:dev \
  -f services/Dockerfile \
  --build-arg SERVICE_NAME=auth_service \
  .

# Run locally
docker run -p 8001:8001 \
  -e SERVICE_HOST=0.0.0.0 \
  -e SERVICE_PORT=8001 \
  auth-service:dev
```

## 🚦 Common Tasks

### Stop All Services

```bash
docker-compose -f docker-compose.services.yml down
```

### Remove All Data

```bash
docker-compose -f docker-compose.services.yml down -v
```

### Scale a Service (with manual port mapping)

```bash
# Start second instance
docker run -p 8011:8001 \
  --name auth-service-2 \
  --network microservices \
  -e SERVICE_HOST=auth-service-2 \
  -e SERVICE_PORT=8001 \
  -e SERVICE_INSTANCE_ID=auth-2 \
  auth-service:latest
```

### View Network Traffic

```bash
# Install Wireshark or use tcpdump
docker exec -it api-gateway tcpdump -i eth0 -A
```

## ✅ Verification Checklist

- [ ] All services running: `docker-compose -f docker-compose.services.yml ps`
- [ ] Gateway responding: `curl http://localhost:8000/health`
- [ ] Service registry populated: `curl http://localhost:8000/registry`
- [ ] Can register user: `curl -X POST http://localhost:8000/auth/register ...`
- [ ] Integration tests passing: `pytest services/tests/ -v`
- [ ] Logs showing correct correlation IDs: `docker logs api-gateway | grep correlation_id`

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose -f docker-compose.services.yml logs`
2. Review documentation: `MICROSERVICES_ARCHITECTURE.md`
3. Run tests: `pytest services/tests/test_integration.py -v`
4. Check service health: `curl http://localhost:8000/health`

## 🎯 Next Steps

1. ✅ Verify all services are running
2. ✅ Test example API calls
3. ✅ Review service logs
4. 📖 Read MICROSERVICES_ARCHITECTURE.md
5. 🚀 Follow MIGRATION_GUIDE.md for production deployment
6. 🔄 Extract additional services (Payment, Transaction, Account)
7. 📊 Set up monitoring and alerting
