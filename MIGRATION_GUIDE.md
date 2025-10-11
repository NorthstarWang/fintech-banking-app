# Microservices Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the monolithic architecture to the new microservices architecture.

## Pre-Migration Checklist

- [ ] Back up production database
- [ ] Document current API endpoints
- [ ] Identify all service dependencies
- [ ] Plan rollback strategy
- [ ] Notify stakeholders of migration window
- [ ] Prepare monitoring and alerting
- [ ] Create feature flags for gradual rollout

## Phase 1: Development & Testing

### Step 1: Extract Services Locally

All services have been extracted to the `services/` directory:

```
services/
├── core/                  # Shared infrastructure
│   ├── correlation_id.py  # Request tracing
│   ├── service_registry.py # Service discovery
│   ├── api_client.py      # Resilient HTTP client
│   └── health_check.py    # Health monitoring
├── auth_service/          # Authentication microservice
├── notification_service/  # Notification microservice
├── analytics_service/     # Analytics microservice
├── api_gateway/           # API Gateway
├── tests/                 # Integration tests
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.services.yml
└── requirements.txt
```

### Step 2: Run Services Locally

Start all services with Docker Compose:

```bash
# Build and start all services
docker-compose -f docker-compose.services.yml up -d

# Verify services are running
docker ps

# Check health of all services
curl http://localhost:8000/health
```

### Step 3: Run Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest services/tests/test_integration.py -v

# Run specific test
pytest services/tests/test_integration.py::TestServiceRegistry::test_register_service -v
```

## Phase 2: Staging Deployment

### Step 1: Prepare Environment

Create `.env.services` with service-specific configuration:

```bash
# Gateway
GATEWAY_HOST=staging-gateway.example.com
GATEWAY_PORT=8000
GATEWAY_API_KEY=staging-gateway-key
ALLOWED_API_KEYS=staging-client-1,staging-client-2

# Auth Service
SERVICE_HOST=staging-auth.example.com
SERVICE_PORT=8001
AUTH_SERVICE_API_KEY=staging-auth-key
JWT_SECRET_KEY=your-production-secret-key

# Notification Service
NOTIFICATION_SERVICE_API_KEY=staging-notification-key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=staging@example.com
SMTP_PASSWORD=your-app-password

# Analytics Service
ANALYTICS_SERVICE_API_KEY=staging-analytics-key

# Logging
LOG_LEVEL=INFO
```

### Step 2: Deploy to Staging

Using Kubernetes (example):

```yaml
# auth-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: your-registry/auth-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: SERVICE_HOST
          valueFrom:
            configMapKeyRef:
              name: service-config
              key: service-host
        - name: SERVICE_PORT
          value: "8001"
        - name: AUTH_SERVICE_API_KEY
          valueFrom:
            secretKeyRef:
              name: service-secrets
              key: auth-api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

Deploy:

```bash
kubectl apply -f auth-service-deployment.yaml
kubectl apply -f notification-service-deployment.yaml
kubectl apply -f analytics-service-deployment.yaml
kubectl apply -f api-gateway-deployment.yaml

# Verify deployment
kubectl get pods -n staging
kubectl describe pod auth-service-xxxxx -n staging
```

### Step 3: Verify Staging Deployment

```bash
# Check service health
curl https://staging-gateway.example.com/health \
  -H "X-API-Key: staging-gateway-key"

# Check service registry
curl https://staging-gateway.example.com/registry \
  -H "X-API-Key: staging-gateway-key"

# Test authentication endpoint
curl -X POST https://staging-gateway.example.com/auth/register \
  -H "X-API-Key: staging-client-1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Step 4: Load Testing

Use tools like Apache JMeter or k6:

```javascript
// k6 load test
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 100,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function() {
  let res = http.get('https://staging-gateway.example.com/health', {
    headers: {
      'X-API-Key': 'staging-gateway-key',
    },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

Run: `k6 run load-test.js`

## Phase 3: Canary Deployment to Production

### Step 1: Gradual Traffic Shift

Route small percentage of traffic to new services:

```python
# Gateway configuration
CANARY_PERCENTAGE = 5  # Start with 5% traffic

if service_name == "auth-service" and random.random() < CANARY_PERCENTAGE / 100:
    client = await client_factory.get_client("auth-service-new")
else:
    client = await client_factory.get_client("auth-service-old")  # Monolith
```

### Step 2: Monitor Metrics

- Error rates
- Response times
- Throughput
- User reports

```bash
# Example monitoring query
rate(http_requests_total{service="auth-service", status="5xx"}[5m]) > 0.01
```

### Step 3: Increase Traffic Gradually

- Day 1: 5% to new services
- Day 2: 10% to new services
- Day 3: 25% to new services
- Day 4: 50% to new services
- Day 5: 100% to new services

### Step 4: Full Switchover

```python
# Update gateway configuration
ROUTE_TO_MONOLITH = False  # Use only new services
```

## Phase 4: Decommission Monolith

### Step 1: Validate All Traffic Flows

```bash
# Check logs for errors
tail -f /var/log/services/*.log | grep -i error

# Verify no requests to monolith
curl -X GET https://production.example.com/api/health
# Should work fine with new services
```

### Step 2: Archive Monolith Code

```bash
# Tag and archive
git tag -a monolith-v1.0 -m "Final monolith version before microservices"
git push origin monolith-v1.0

# Backup database
pg_dump production_db > backup_production_$(date +%Y%m%d).sql
```

### Step 3: Remove Monolith Services

```bash
# Stop monolith processes
systemctl stop monolith-api

# Remove from deployment
kubectl delete deployment monolith-api

# Clean up resources
docker rmi monolith:latest
```

## Handling Failures During Migration

### Service Down

If a new service fails:

```python
# Automatic fallback to monolith
try:
    result = await new_service_client.request(...)
except ServiceUnavailableError:
    logger.warning("New service down, falling back to monolith")
    result = await monolith_client.request(...)
```

### Data Inconsistency

If data doesn't match between old and new services:

1. Identify discrepancy
2. Investigate root cause
3. Run data sync job
4. Resume migration from current percentage

```bash
# Data sync script
python scripts/sync_data.py --source monolith --destination auth-service
```

### Rollback

If critical issues occur:

```bash
# Immediate rollback
kubectl patch service api-gateway -p \
  '{"spec":{"selector":{"version":"v1"}}}'

# Verify rollback
curl https://production.example.com/health
```

## Monitoring During Migration

### Alerting Rules

```yaml
# Prometheus alerts
- alert: HighErrorRateNewServices
  expr: rate(http_requests_total{service=~"auth|notification|analytics", status="5xx"}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate in {{ $labels.service }}"

- alert: ServiceDown
  expr: up{service=~"auth|notification|analytics"} == 0
  for: 2m
  annotations:
    summary: "{{ $labels.service }} is down"

- alert: HighResponseTime
  expr: histogram_quantile(0.95, http_request_duration_seconds{service=~"auth|notification|analytics"}) > 1
  for: 10m
  annotations:
    summary: "High response time in {{ $labels.service }}"
```

### Dashboards

Create Grafana dashboards for:
- Service availability
- Response times (p50, p95, p99)
- Error rates
- Throughput
- Resource usage (CPU, Memory)

## Post-Migration

### Step 1: Performance Tuning

Analyze metrics and optimize:

```bash
# Identify slow endpoints
SELECT endpoint, avg(response_time) FROM metrics
GROUP BY endpoint
ORDER BY avg(response_time) DESC
LIMIT 10;

# Add caching
# Optimize database queries
# Implement batching
```

### Step 2: Documentation Update

- Update API documentation
- Create runbooks for on-call engineers
- Document new monitoring dashboards
- Update deployment procedures

### Step 3: Team Training

- Cross-train teams on new architecture
- Document service ownership
- Set up on-call rotations
- Create troubleshooting guides

## Troubleshooting Common Issues

### Issue: High Latency After Migration

**Symptoms**: Response times increased 2-3x after migration

**Causes**:
- Network latency between services
- Database connection pooling issues
- Missing caches

**Resolution**:
1. Check network latency: `ping service-host`
2. Monitor database connections: `SELECT count(*) FROM pg_stat_activity`
3. Implement caching for frequently accessed data
4. Use persistent connections

### Issue: Intermittent Failures

**Symptoms**: Some requests fail, some succeed

**Causes**:
- Retry logic not working properly
- Load balancing issues
- Circuit breaker incorrectly configured

**Resolution**:
1. Check retry logic in api_client.py
2. Verify service discovery is finding all instances
3. Check circuit breaker thresholds
4. Review error logs for pattern

### Issue: Data Sync Problems

**Symptoms**: Auth service has different user data than monolith

**Causes**:
- Services not reading from same database
- Async writes causing delays
- Migration script missed data

**Resolution**:
1. Verify both services connect to same database
2. Implement read-your-writes consistency
3. Run full data reconciliation
4. Monitor data consistency metrics

## Success Criteria

✓ All services deployed to production
✓ 100% traffic routed to new services
✓ Error rate < 0.1%
✓ Response time p95 < 500ms
✓ All health checks passing
✓ Monitoring and alerting working
✓ Team trained on new architecture
✓ Documentation updated
✓ No critical issues reported

## Next Steps

1. Extract more services (Payment, Transaction, Account)
2. Implement service mesh (Istio)
3. Add event-driven communication (Kafka, RabbitMQ)
4. Implement distributed tracing (Jaeger)
5. Add API versioning and GraphQL gateway
