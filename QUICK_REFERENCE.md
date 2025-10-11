# Quick Reference Card

Essential commands and procedures for microservices management.

## 🚀 Quick Start (First Time)

```bash
# 1. Build Docker images
docker-compose -f docker-compose.services.yml build

# 2. Start services locally
docker-compose -f docker-compose.services.yml up -d

# 3. Test health
curl http://localhost:8000/health

# 4. View logs
docker-compose -f docker-compose.services.yml logs -f
```

## ☸️ Kubernetes Management

### Deployment

```bash
# Deploy namespace & base config
kubectl apply -f k8s/base/

# Deploy specific service
kubectl apply -f k8s/services/api-gateway-deployment.yaml

# Deploy all services
kubectl apply -f k8s/services/

# Check status
kubectl get pods -n fintech-services
kubectl get svc -n fintech-services
kubectl get hpa -n fintech-services
```

### Monitoring

```bash
# Port forward to Prometheus
kubectl port-forward -n fintech-services svc/prometheus 9090:9090

# Port forward to Grafana
kubectl port-forward -n fintech-services svc/grafana 3000:3000

# Port forward to Jaeger
kubectl port-forward -n fintech-services svc/jaeger 16686:16686
```

### Debugging

```bash
# Get pod details
kubectl describe pod <pod-name> -n fintech-services

# View pod logs
kubectl logs <pod-name> -n fintech-services -f

# Execute command in pod
kubectl exec -it <pod-name> -n fintech-services -- bash

# Get into pod shell
kubectl exec -it <pod-name> -n fintech-services -- /bin/sh
```

### Scaling

```bash
# Manual scale
kubectl scale deployment auth-service --replicas=5 -n fintech-services

# View HPA status
kubectl get hpa -n fintech-services
kubectl describe hpa auth-service-hpa -n fintech-services

# Update HPA limits
kubectl patch hpa auth-service-hpa -n fintech-services -p \
  '{"spec":{"minReplicas":3,"maxReplicas":15}}'
```

### Updating

```bash
# Update service image
kubectl set image deployment/auth-service \
  auth-service=fintech-services/auth-service:v1.0.1 \
  -n fintech-services

# Monitor rollout
kubectl rollout status deployment/auth-service -n fintech-services

# Rollback if needed
kubectl rollout undo deployment/auth-service -n fintech-services
```

## 🔍 Health Checks

### Service Status

```bash
# Check service endpoint
kubectl exec -it <pod> -n fintech-services -- \
  curl -s http://localhost:8001/health | jq

# Check service registry
kubectl exec -it <gateway-pod> -n fintech-services -- \
  curl -s -H "X-API-Key: gateway-key-dev" \
  http://localhost:8000/registry | jq
```

### Resource Usage

```bash
# Pod resource usage
kubectl top pod -n fintech-services
kubectl top pod -n fintech-services -l app=auth-service

# Node resource usage
kubectl top nodes
```

### Network Connectivity

```bash
# Test DNS resolution
kubectl exec -it <pod> -n fintech-services -- \
  nslookup auth-service.fintech-services.svc.cluster.local

# Test service connectivity
kubectl exec -it <pod> -n fintech-services -- \
  curl http://auth-service:8001/health
```

## 📊 Monitoring Queries

### Prometheus

```promql
# Service availability
sum by (job) (rate(http_requests_total{status="2xx"}[5m])) / sum by (job) (rate(http_requests_total[5m]))

# Error rate
sum by (job) (rate(http_requests_total{status="5xx"}[5m])) / sum by (job) (rate(http_requests_total[5m]))

# Latency P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Pod memory usage
container_memory_usage_bytes{pod=~".*-service.*"}

# Pod CPU usage
rate(container_cpu_usage_seconds_total{pod=~".*-service.*"}[5m])
```

## 🔧 Common Operations

### Restart Service

```bash
# Rolling restart
kubectl rollout restart deployment/auth-service -n fintech-services

# Immediate restart (might cause downtime)
kubectl delete pod -l app=auth-service -n fintech-services
```

### Clear Circuit Breakers

```bash
# In single pod
kubectl exec -it <pod> -n fintech-services -- \
  curl -X POST http://localhost:8001/circuit-breakers/reset

# In all pods
for pod in $(kubectl get pods -n fintech-services -o name); do
  kubectl exec -it $pod -n fintech-services -- \
    curl -X POST http://localhost:8001/circuit-breakers/reset 2>/dev/null
done
```

### View Service Traces

```bash
# Access Jaeger UI
open http://localhost:16686

# Query specific service
# In Jaeger UI: Select service → View traces
```

### Export Metrics

```bash
# Export to Prometheus format
kubectl exec -it <pod> -n fintech-services -- \
  curl http://localhost:8001/metrics > metrics.txt

# Export logs with timestamps
kubectl logs <pod> -n fintech-services --timestamps=true > logs.txt
```

## 🚨 Incident Response

### Service Down

```bash
# 1. Check pod status
kubectl get pods -n fintech-services -l app=<service>

# 2. Check logs
kubectl logs -n fintech-services -l app=<service> --tail=100 | grep -i error

# 3. Restart if hung
kubectl delete pod -l app=<service> -n fintech-services

# 4. Monitor recovery
kubectl get pods -n fintech-services -w
```

### High Error Rate

```bash
# 1. Identify affected service
# Check Prometheus: rate(http_requests_total{status="5xx"}[5m])

# 2. Check dependent services
kubectl exec -it <service-pod> -n fintech-services -- \
  curl -s http://localhost:8001/health/detailed | jq

# 3. Reset circuit breakers
kubectl exec -it <pod> -n fintech-services -- \
  curl -X POST http://localhost:8001/circuit-breakers/reset

# 4. Restart if needed
kubectl rollout restart deployment/<service> -n fintech-services
```

### High Memory Usage

```bash
# 1. Identify pod
kubectl top pods -n fintech-services --sort-by=memory

# 2. Check logs for memory leak
kubectl logs <pod> -n fintech-services | tail -500

# 3. Restart pod
kubectl delete pod <pod> -n fintech-services

# 4. Monitor
kubectl top pod <pod> -n fintech-services --containers -w
```

## 📝 Logging & Events

### View Events

```bash
# Recent cluster events
kubectl get events -n fintech-services --sort-by='.lastTimestamp'

# Watch events live
kubectl get events -n fintech-services -w

# Pod-specific events
kubectl describe pod <pod> -n fintech-services
```

### View Pod Logs

```bash
# Last 100 lines
kubectl logs <pod> -n fintech-services --tail=100

# Stream live logs
kubectl logs <pod> -n fintech-services -f

# Previous pod logs (if crashed)
kubectl logs <pod> -n fintech-services --previous

# All containers in pod
kubectl logs <pod> -n fintech-services --all-containers=true
```

### Log Search

```bash
# Grep in logs
kubectl logs -n fintech-services -l app=auth-service | grep "error"

# Get logs since time
kubectl logs <pod> -n fintech-services --since=1h

# Get logs for specific timeframe
kubectl logs <pod> -n fintech-services --timestamps=true \
  | awk '$1 >= "2024-01-15T10:00:00"'
```

## 🔒 Security

### Check Network Policies

```bash
# List policies
kubectl get networkpolicies -n fintech-services

# Describe policy
kubectl describe networkpolicy <policy-name> -n fintech-services

# Apply security policies
kubectl apply -f k8s/security/
```

### Verify mTLS

```bash
# Check certificate
kubectl get secret -n fintech-services | grep tls

# View certificate details
kubectl get secret <cert-secret> -n fintech-services -o yaml | \
  grep tls.crt | base64 -d | openssl x509 -text -noout
```

### Check RBAC

```bash
# List service accounts
kubectl get sa -n fintech-services

# View role bindings
kubectl get rolebindings -n fintech-services
kubectl get clusterrolebindings | grep fintech
```

## 💾 Backup & Recovery

### Database Backup

```bash
# Backup
kubectl exec -it postgres-0 -n fintech-services -- \
  pg_dump $DATABASE_URL | gzip > db_backup_$(date +%Y%m%d).sql.gz

# Restore
kubectl exec -it postgres-0 -n fintech-services -- \
  psql $DATABASE_URL < backup.sql

# List backups
ls -lh *.sql.gz
```

### Event Store Backup

```bash
# Export events
kubectl exec -it transaction-service-0 -n fintech-services -- \
  curl http://localhost:8004/events/export > events_backup.json

# Import events
kubectl exec -it transaction-service-0 -n fintech-services -- \
  curl -X POST -d @events_backup.json \
  http://localhost:8004/events/import
```

## 🧪 Testing

### Smoke Test

```bash
# API Gateway
curl -s http://localhost:8000/health | jq

# Auth Service
curl -s http://localhost:8001/health | jq

# Service Discovery
curl -s -H "X-API-Key: gateway-key-dev" \
  http://localhost:8000/registry | jq
```

### Load Test

```bash
# Using k6
kubectl apply -f k8s/testing/k6-loadtest.yaml
kubectl logs -n fintech-services -l job=k6-loadtest -f

# Using Apache Bench
ab -n 1000 -c 100 http://localhost:8000/health
```

### Chaos Test

```bash
# Kill random pod
kubectl delete pod $(kubectl get pods -n fintech-services \
  -o name | shuf -n 1)

# Monitor recovery
kubectl get pods -n fintech-services -w

# Simulate latency
kubectl exec -it <pod> -n fintech-services -- \
  tc qdisc add dev eth0 root netem delay 500ms

# Simulate packet loss
kubectl exec -it <pod> -n fintech-services -- \
  tc qdisc add dev eth0 root netem loss 5%
```

## 📚 Useful URLs (when port-forwarded)

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Jaeger**: http://localhost:16686
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8001
- **Notification**: http://localhost:8002
- **Analytics**: http://localhost:8003

## 🔗 Quick Links

- Documentation: `docs/`
- Runbooks: `docs/OPERATIONAL_RUNBOOKS.md`
- Incidents: `docs/INCIDENT_RESPONSE.md`
- Architecture: `MICROSERVICES_ARCHITECTURE.md`
- Deployment: `PRODUCTION_DEPLOYMENT_GUIDE.md`

---

**Print this card and keep it handy!**
