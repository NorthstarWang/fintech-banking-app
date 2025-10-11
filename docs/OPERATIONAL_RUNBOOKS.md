# Operational Runbooks

Production-grade runbooks for common operational tasks and incident response.

## Table of Contents

1. [Service Deployment](#service-deployment)
2. [Common Incidents](#common-incidents)
3. [Scaling Operations](#scaling-operations)
4. [Backup & Recovery](#backup--recovery)
5. [Performance Tuning](#performance-tuning)

---

## Service Deployment

### Deploying a New Service Version

**Prerequisites**:
- Docker image built and pushed to registry
- Kubernetes cluster access
- kubectl configured

**Steps**:

```bash
# 1. Update deployment image
kubectl set image deployment/auth-service \
  auth-service=fintech-services/auth-service:v2.0.0 \
  -n fintech-services

# 2. Monitor rollout
kubectl rollout status deployment/auth-service -n fintech-services --timeout=5m

# 3. Verify health
kubectl get pods -n fintech-services -l app=auth-service
kubectl logs -n fintech-services -l app=auth-service --tail=100

# 4. Check metrics
# Navigate to Prometheus/Grafana dashboard and verify metrics
```

**Rollback if needed**:

```bash
# Automatic rollback
kubectl rollout undo deployment/auth-service -n fintech-services

# Verify rollback
kubectl rollout status deployment/auth-service -n fintech-services
```

### Scaling a Service

**Manual scaling**:

```bash
# Scale to specific number of replicas
kubectl scale deployment auth-service --replicas=5 -n fintech-services

# Verify scaling
kubectl get deployment auth-service -n fintech-services
```

**Check auto-scaling status**:

```bash
# View HPA status
kubectl get hpa -n fintech-services
kubectl describe hpa auth-service-hpa -n fintech-services

# View HPA metrics
kubectl top pods -n fintech-services -l app=auth-service
```

---

## Common Incidents

### Incident: Service Not Responding

**Symptoms**:
- API returning 503 Service Unavailable
- High latency
- Timeouts

**Investigation**:

```bash
# 1. Check pod status
kubectl get pods -n fintech-services -l app=auth-service

# 2. Check logs
kubectl logs -n fintech-services -l app=auth-service --tail=200 | grep -i error

# 3. Check resource usage
kubectl top pods -n fintech-services -l app=auth-service

# 4. Check health endpoints
kubectl exec -it <pod-name> -n fintech-services -- \
  curl -s http://localhost:8001/health | jq

# 5. Check circuit breaker status
kubectl exec -it <pod-name> -n fintech-services -- \
  curl -s http://localhost:8001/circuit-breakers | jq
```

**Resolution**:

```bash
# Option 1: Restart pods (rolling restart)
kubectl rollout restart deployment/auth-service -n fintech-services

# Option 2: Scale down and up
kubectl scale deployment auth-service --replicas=0 -n fintech-services
sleep 10
kubectl scale deployment auth-service --replicas=3 -n fintech-services

# Option 3: Check and fix issues
# - Increase resource limits if high memory/CPU
# - Check configuration
# - Review recent changes
# - Check dependency services (database, cache)
```

### Incident: High Error Rate

**Symptoms**:
- Error rate > 1%
- Alert: "HighErrorRate"
- Users reporting failures

**Investigation**:

```bash
# 1. Check Prometheus for error patterns
# Query: rate(http_requests_total{status="5xx"}[5m])
# Query: rate(http_requests_total{job="auth-service",status="5xx"}[5m])

# 2. Check logs for errors
kubectl logs -n fintech-services -l app=auth-service \
  --timestamps=true --tail=500 | grep -i "error\|exception\|failed"

# 3. Check dependent services
kubectl get pods -n fintech-services
kubectl logs -n fintech-services -l app=notification-service --tail=100

# 4. Check database connectivity
kubectl exec -it <pod-name> -n fintech-services -- \
  curl -s http://localhost:8001/health/detailed | jq '.checks'
```

**Resolution**:

```bash
# 1. Identify root cause from logs
# Look for: database errors, connection timeouts, dependency failures

# 2. If database issue
# - Check database service
# - Check connection pool settings
# - Increase connections if needed

# 3. If dependency issue
# - Check dependent service status
# - Reset circuit breakers if needed:
kubectl exec -it <pod-name> -n fintech-services -- \
  curl -X POST http://localhost:8001/circuit-breakers/reset

# 4. If configuration issue
# - Update ConfigMap
# - Restart pods to pick up new config

# 5. If memory leak
# - Monitor heap usage
# - Restart affected pods
# - Review recent code changes
```

### Incident: Database Connection Issues

**Symptoms**:
- "Connection refused" errors
- "Connection pool exhausted"
- Slow queries

**Investigation**:

```bash
# 1. Check database accessibility
kubectl exec -it <service-pod> -n fintech-services -- \
  telnet db-host 5432

# 2. Check open connections
# On database server:
SELECT count(*) FROM pg_stat_activity;
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# 3. Check service logs
kubectl logs -n fintech-services -l app=auth-service | grep -i "connection"
```

**Resolution**:

```bash
# 1. Increase connection pool size
kubectl set env deployment/auth-service \
  DB_POOL_SIZE=20 \
  -n fintech-services

# 2. Restart pods
kubectl rollout restart deployment/auth-service -n fintech-services

# 3. Check database performance
# - Review slow query log
# - Check indices
# - Analyze query plans

# 4. Scale database if needed
# - Add read replicas
# - Increase database resources
```

### Incident: Memory Leak

**Symptoms**:
- Memory usage continuously increasing
- Alert: "HighMemoryUsage"
- Eventually OOMKilled

**Investigation**:

```bash
# 1. Monitor memory trend
kubectl top pod <pod-name> -n fintech-services --containers

# 2. Check Java heap (if applicable)
kubectl exec -it <pod-name> -n fintech-services -- \
  jmap -heap <pid>

# 3. Generate heap dump (if applicable)
kubectl exec -it <pod-name> -n fintech-services -- \
  jmap -dump:live,file=/tmp/heap.bin <pid>

# 4. Check application logs
kubectl logs -n fintech-services <pod-name> | tail -200
```

**Resolution**:

```bash
# 1. Immediate: Restart pods
kubectl rollout restart deployment/auth-service -n fintech-services

# 2. Investigate code
# - Check for unclosed resources
# - Look for memory accumulation patterns
# - Review recent changes

# 3. Adjust memory limits if legitimate growth
kubectl set resources deployment/auth-service \
  --limits=memory=1Gi \
  -n fintech-services

# 4. Deploy fix after investigation
kubectl set image deployment/auth-service \
  auth-service=fintech-services/auth-service:vX.X.X-hotfix \
  -n fintech-services
```

### Incident: Cascading Failures

**Symptoms**:
- Multiple services failing
- Rapid error rate increase
- Circuit breakers opening

**Investigation**:

```bash
# 1. Identify which service failed first
# Check timestamps in logs and metrics

# 2. Check service dependency graph
# Auth Service -> Account Service -> Payment Service

# 3. Check circuit breaker states
kubectl exec -it <pod-name> -n fintech-services -- \
  curl http://localhost:8001/circuit-breakers | jq
```

**Resolution - Isolation**:

```bash
# 1. Isolate the failing service
kubectl scale deployment failing-service --replicas=0 -n fintech-services

# 2. Reset circuit breakers on dependent services
kubectl exec -it <pod-name> -n fintech-services -- \
  curl -X POST http://localhost:8001/circuit-breakers/reset

# 3. Restart dependent services
kubectl rollout restart deployment/auth-service -n fintech-services
kubectl rollout restart deployment/account-service -n fintech-services
```

**Resolution - Recovery**:

```bash
# 1. Fix the root cause service
# - Review logs
# - Check dependencies
# - Deploy fix

# 2. Scale back up
kubectl scale deployment failing-service --replicas=2 -n fintech-services

# 3. Monitor metrics
# Watch for error rates returning to normal

# 4. Clear circuit breakers if needed
# and restart dependent services again
```

---

## Scaling Operations

### Horizontal Scaling

**Auto-scaling enabled configurations**:

```bash
# View current HPA
kubectl get hpa -n fintech-services

# View HPA metrics
kubectl get hpa auth-service-hpa -n fintech-services -w

# Manually adjust HPA limits
kubectl patch hpa auth-service-hpa -n fintech-services -p \
  '{"spec":{"minReplicas":3,"maxReplicas":15}}'
```

**Manual scaling**:

```bash
# Scale a service up
kubectl scale deployment auth-service --replicas=5 -n fintech-services

# Scale all services
for service in auth-service notification-service analytics-service; do
  kubectl scale deployment $service --replicas=3 -n fintech-services
done

# Wait for scaling to complete
kubectl wait --for=condition=Progressing=True \
  deployment/auth-service \
  -n fintech-services \
  --timeout=5m
```

### Vertical Scaling

```bash
# Increase resource limits for a service
kubectl set resources deployment/auth-service \
  --requests=memory=512Mi,cpu=500m \
  --limits=memory=1Gi,cpu=1 \
  -n fintech-services

# Verify changes
kubectl get deployment auth-service -o yaml -n fintech-services | \
  grep -A 4 "resources:"
```

---

## Backup & Recovery

### Database Backup

```bash
# Create backup
kubectl exec -it <db-pod> -n fintech-services -- \
  pg_dump fintech_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup to persistent volume
kubectl exec -it <db-pod> -n fintech-services -- \
  pg_dump fintech_db | gzip > /backups/db_backup_$(date +%Y%m%d).sql.gz
```

### Service Restore

```bash
# Restore from backup
kubectl exec -it <db-pod> -n fintech-services -- \
  psql fintech_db < backup_20240115_120000.sql

# Verify restore
kubectl exec -it <service-pod> -n fintech-services -- \
  curl http://localhost:8001/health
```

### Event Store Recovery

```bash
# Export event store (for transaction service)
kubectl exec -it transaction-service-xxxx -n fintech-services -- \
  curl http://localhost:8004/events/export > events_backup.json

# Restore event store
kubectl exec -it transaction-service-xxxx -n fintech-services -- \
  curl -X POST -d @events_backup.json \
  http://localhost:8004/events/import
```

---

## Performance Tuning

### Optimize Database Queries

```bash
# Enable query logging
kubectl set env deployment/auth-service \
  POSTGRES_LOG_MIN_DURATION_STATEMENT=1000 \
  -n fintech-services

# Check slow query log
# SELECT query, mean_time FROM pg_stat_statements
# ORDER BY mean_time DESC LIMIT 10;

# Add indices if needed
# CREATE INDEX idx_users_email ON users(email);
```

### Tune Cache Settings

```bash
# Increase cache TTL
kubectl set env deployment/analytics-service \
  CACHE_TTL_SECONDS=600 \
  -n fintech-services

# Clear cache if needed
kubectl exec -it analytics-service-xxxx -n fintech-services -- \
  curl -X POST http://localhost:8003/cache/clear
```

### Monitor Resource Usage

```bash
# Real-time monitoring
kubectl top pods -n fintech-services --containers

# Resource trends
kubectl top pods -n fintech-services -l app=auth-service --sort-by=memory

# Get detailed resource info
kubectl describe node <node-name>
```

### Network Optimization

```bash
# Check network policies
kubectl get networkpolicies -n fintech-services

# Monitor network traffic
kubectl exec -it <pod> -n fintech-services -- \
  tcpdump -i eth0 -n 'tcp port 5432'

# Test inter-pod latency
kubectl exec -it <pod1> -n fintech-services -- \
  ping <pod2>.fintech-services.svc.cluster.local
```

---

## Monitoring & Observability

### Access Prometheus

```bash
# Port forward to Prometheus
kubectl port-forward -n fintech-services svc/prometheus 9090:9090

# Access at http://localhost:9090
```

### Access Grafana

```bash
# Port forward to Grafana
kubectl port-forward -n fintech-services svc/grafana 3000:3000

# Access at http://localhost:3000
```

### View Service Traces

```bash
# Port forward to Jaeger/Tempo (if installed)
kubectl port-forward -n fintech-services svc/jaeger 16686:16686

# Access at http://localhost:16686
```

### Export Metrics

```bash
# Get current metrics for a service
kubectl exec -it auth-service-xxxx -n fintech-services -- \
  curl http://localhost:8001/metrics

# Export to file
kubectl logs -n fintech-services -l app=auth-service --timestamps=true > logs.txt
```

---

## Emergency Procedures

### Full Cluster Restart

```bash
# 1. Backup all data
kubectl exec -it db-pod -n fintech-services -- pg_dump fintech_db > backup.sql

# 2. Scale down all services gracefully
kubectl scale deployment --all --replicas=0 -n fintech-services

# 3. Wait for pods to terminate
kubectl wait --for=delete pod --all -n fintech-services --timeout=5m

# 4. Scale back up
for service in api-gateway auth-service notification-service analytics-service; do
  kubectl scale deployment $service --replicas=2 -n fintech-services
done

# 5. Monitor startup
kubectl get pods -n fintech-services -w
```

### Circuit Breaker Reset All

```bash
# Reset all circuit breakers across all services
for pod in $(kubectl get pods -n fintech-services -o name); do
  kubectl exec -it $pod -n fintech-services -- \
    curl -X POST http://localhost:8001/circuit-breakers/reset 2>/dev/null
done
```

### Drain Node for Maintenance

```bash
# 1. Cordon node
kubectl cordon <node-name>

# 2. Drain pods gracefully
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 3. Perform maintenance

# 4. Uncordon node
kubectl uncordon <node-name>

# 5. Monitor pod rescheduling
kubectl get pods -n fintech-services -w
```

---

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Queries](https://prometheus.io/docs/prometheus/latest/querying/)
- [Service Runbooks Best Practices](https://sre.google/sre-book/)
