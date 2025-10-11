# Production Deployment Guide

Complete guide for deploying production-grade fintech microservices on Kubernetes.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                               │
└──────────────────────────────────────┬──────────────────────────┘
                                       │
                            ┌──────────▼────────────┐
                            │  Load Balancer / Ingress
                            │  (TLS Termination)   │
                            └──────────┬────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────┐
        │                              │                          │
        ▼                              ▼                          ▼
    ┌────────────┐           ┌──────────────────┐      ┌──────────────┐
    │ API        │           │ Service 1        │      │ Service N    │
    │ Gateway    │ ─mTLS──▶  │ (Auth Service)   │      │ (Risk Svc)   │
    │ (Port 443) │           │                  │      │              │
    └──────┬─────┘           └────────┬─────────┘      └─────┬────────┘
           │                          │                       │
           ├──── Service Discovery ───┼───────────────────────┤
           │     (Kubernetes DNS)     │                       │
           │                          │                       │
        ┌──────────────────────────────────────────────────────────────┐
        │  Observability Stack                                        │
        │  ┌─────────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐  │
        │  │ Prometheus  │  │ Grafana │  │  Jaeger  │  │ Loki    │  │
        │  └─────────────┘  └─────────┘  └──────────┘  └─────────┘  │
        └──────────────────────────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────┐
    │  Data Layer                         │
    │  ┌────────────┐  ┌─────────────┐  │
    │  │ PostgreSQL │  │ Redis Cache │  │
    │  └────────────┘  └─────────────┘  │
    └─────────────────────────────────────┘
```

## Prerequisites

- Kubernetes 1.24+
- kubectl configured with cluster access
- Docker for image building
- Helm 3+ (optional but recommended)
- Prometheus & Grafana installed
- PostgreSQL 13+ (managed or self-hosted)

## Phase 1: Pre-Deployment Setup

### 1.1 Create Namespace & RBAC

```bash
# Create namespace
kubectl create namespace fintech-services

# Apply RBAC configuration
kubectl apply -f k8s/base/service-account.yaml

# Verify
kubectl get ns fintech-services
kubectl get sa -n fintech-services
```

### 1.2 Create Secrets

```bash
# Create secrets from environment variables
kubectl create secret generic services-secrets \
  --from-literal=GATEWAY_API_KEY=$GATEWAY_API_KEY \
  --from-literal=JWT_SECRET_KEY=$JWT_SECRET_KEY \
  --from-literal=DATABASE_URL=$DATABASE_URL \
  -n fintech-services

# Verify (DO NOT output values!)
kubectl get secret services-secrets -n fintech-services
```

### 1.3 Create ConfigMaps

```bash
# Create configuration
kubectl apply -f k8s/base/configmap.yaml

# Verify
kubectl get configmap services-config -n fintech-services
```

### 1.4 Setup Networking

```bash
# Create network policies
kubectl apply -f k8s/base/network-policy.yaml

# Verify policies
kubectl get networkpolicies -n fintech-services
```

## Phase 2: Database Setup

### 2.1 Database Initialization

```bash
# Create database and tables
psql $DATABASE_URL << EOF
  CREATE SCHEMA IF NOT EXISTS fintech;

  CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(12, 2),
    transaction_type VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE INDEX idx_users_email ON users(email);
  CREATE INDEX idx_transactions_user_id ON transactions(user_id);
  CREATE INDEX idx_transactions_created_at ON transactions(created_at);
EOF
```

### 2.2 Backup Strategy

```bash
# Create automated backups (CronJob)
kubectl apply -f k8s/backup/database-backup-cronjob.yaml

# Initial backup
kubectl exec -it postgres-0 -n fintech-services -- \
  pg_dump $DATABASE_URL | gzip > db_backup_$(date +%Y%m%d).sql.gz
```

## Phase 3: Observability Stack

### 3.1 Deploy Prometheus

```bash
# Create Prometheus configuration
kubectl apply -f k8s/monitoring/prometheus-config.yaml

# Deploy Prometheus
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

# Verify
kubectl get pods -n fintech-services -l app=prometheus
```

### 3.2 Deploy Grafana

```bash
# Deploy Grafana
kubectl apply -f k8s/monitoring/grafana-deployment.yaml

# Get Grafana password
GRAFANA_PASSWORD=$(kubectl get secret grafana -n fintech-services \
  -o jsonpath='{.data.admin-password}' | base64 --decode)

# Port forward to Grafana
kubectl port-forward -n fintech-services svc/grafana 3000:3000

# Access at http://localhost:3000 with admin:$GRAFANA_PASSWORD
```

### 3.3 Deploy Jaeger for Tracing

```bash
# Deploy Jaeger
kubectl apply -f k8s/monitoring/jaeger-deployment.yaml

# Port forward
kubectl port-forward -n fintech-services svc/jaeger 16686:16686

# Access at http://localhost:16686
```

## Phase 4: Service Deployment

### 4.1 Build Docker Images

```bash
# Build all service images
for service in api-gateway auth-service notification-service analytics-service transaction-service account-service payment-service risk-service; do
  docker build \
    -t fintech-services/$service:v1.0.0 \
    -f services/Dockerfile \
    --build-arg SERVICE_NAME=${service//-/_} \
    .

  # Push to registry
  docker push fintech-services/$service:v1.0.0
done
```

### 4.2 Deploy Services in Order

```bash
# 1. Deploy database (if not managed)
kubectl apply -f k8s/services/postgres-statefulset.yaml
kubectl wait --for=condition=Ready pod -l app=postgres -n fintech-services --timeout=5m

# 2. Deploy API Gateway first (depends on all services)
kubectl apply -f k8s/services/api-gateway-deployment.yaml
kubectl rollout status deployment/api-gateway -n fintech-services --timeout=5m

# 3. Deploy core services
kubectl apply -f k8s/services/auth-service-deployment.yaml
kubectl apply -f k8s/services/notification-service-deployment.yaml
kubectl apply -f k8s/services/analytics-service-deployment.yaml
kubectl apply -f k8s/services/transaction-service-deployment.yaml
kubectl apply -f k8s/services/account-service-deployment.yaml
kubectl apply -f k8s/services/payment-service-deployment.yaml
kubectl apply -f k8s/services/risk-service-deployment.yaml

# 4. Wait for all services
kubectl wait --for=condition=Ready pod --all -n fintech-services --timeout=10m
```

### 4.3 Verify Deployments

```bash
# Check pod status
kubectl get pods -n fintech-services

# Check service discovery
kubectl exec -it $(kubectl get pods -n fintech-services \
  -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') \
  -n fintech-services -- \
  curl -s http://localhost:8000/registry | jq

# Check health endpoints
for pod in $(kubectl get pods -n fintech-services -o name); do
  kubectl exec -it $pod -n fintech-services -- \
    curl -s http://localhost:8001/health 2>/dev/null | jq -c '.status'
done
```

## Phase 5: Testing & Validation

### 5.1 Smoke Tests

```bash
# Test API Gateway health
kubectl exec -it $(kubectl get pods -n fintech-services \
  -l app=api-gateway -o jsonpath='{.items[0].metadata.name}') \
  -n fintech-services -- \
  curl -s http://localhost:8000/health | jq

# Test service registration
GATEWAY_POD=$(kubectl get pods -n fintech-services \
  -l app=api-gateway -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $GATEWAY_POD -n fintech-services -- \
  curl -s -H "X-API-Key: gateway-key-dev" \
  http://localhost:8000/registry | jq '.[] | length'

# Test auth flow
kubectl exec -it $GATEWAY_POD -n fintech-services -- \
  curl -s -X POST http://localhost:8000/auth/register \
  -H "X-API-Key: client-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }' | jq '.id'
```

### 5.2 Load Testing

```bash
# Using k6
kubectl apply -f k8s/testing/k6-loadtest.yaml

# Monitor load test
kubectl logs -n fintech-services -l job=k6-loadtest -f
```

### 5.3 Chaos Engineering

```bash
# Kill random pod
kubectl delete pod $(kubectl get pods -n fintech-services \
  -o name | shuf -n 1)

# Monitor recovery
kubectl get pods -n fintech-services -w

# Simulate network latency
kubectl apply -f k8s/testing/chaos-network-delay.yaml
```

## Phase 6: Production Hardening

### 6.1 Enable mTLS

```bash
# Create certificates
./scripts/generate-mtls-certs.sh

# Create certificate secrets
for service in auth-service notification-service analytics-service; do
  kubectl create secret tls $service-tls \
    --cert=certs/$service.crt \
    --key=certs/$service.key \
    -n fintech-services
done

# Update deployments to use mTLS
kubectl patch deployment auth-service -n fintech-services -p \
  '{"spec":{"template":{"spec":{"volumes":[{"name":"tls","secret":{"secretName":"auth-service-tls"}}]}}}}'
```

### 6.2 Enable Pod Security Policies

```bash
# Apply PSP
kubectl apply -f k8s/security/pod-security-policy.yaml

# Bind to namespace
kubectl apply -f k8s/security/psp-rolebinding.yaml
```

### 6.3 Resource Quotas

```bash
# Set resource quotas
kubectl apply -f k8s/security/resource-quota.yaml

# Verify
kubectl describe resourcequota -n fintech-services
```

### 6.4 Network Isolation

```bash
# Deny all ingress by default
kubectl apply -f k8s/security/default-deny-ingress.yaml

# Allow only from API Gateway
kubectl apply -f k8s/security/allow-from-gateway.yaml
```

## Phase 7: Monitoring & Alerting

### 7.1 Configure Alerts

```bash
# Create alert rules
kubectl apply -f k8s/monitoring/prometheus-rules.yaml

# Verify rules loaded
kubectl exec -it prometheus-0 -n fintech-services -- \
  curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules | length'
```

### 7.2 Setup AlertManager

```bash
# Configure AlertManager for Slack/email/PagerDuty
kubectl apply -f k8s/monitoring/alertmanager-config.yaml

# Verify
kubectl get pods -n fintech-services -l app=alertmanager
```

### 7.3 Create Dashboards

```bash
# Import Grafana dashboards
# Prometheus: https://grafana.com/grafana/dashboards/3662/
# Kubernetes: https://grafana.com/grafana/dashboards/7249/

# Or create custom via Grafana UI at http://localhost:3000
```

## Phase 8: Backup & Disaster Recovery

### 8.1 Etcd Backup

```bash
# Backup Kubernetes etcd
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /backup/etcd_$(date +%Y%m%d_%H%M%S).db
```

### 8.2 Application Data Backup

```bash
# Database backup
kubectl exec -it postgres-0 -n fintech-services -- \
  pg_dump $DATABASE_URL | gzip > /backup/db_$(date +%Y%m%d).sql.gz

# Event store backup (Transaction Service)
kubectl exec -it transaction-service-0 -n fintech-services -- \
  curl http://localhost:8004/events/export > /backup/events_$(date +%Y%m%d).json
```

## Phase 9: Post-Deployment Verification

### Checklist

- [ ] All pods running and ready
- [ ] Services accessible via API Gateway
- [ ] Metrics flowing to Prometheus
- [ ] Grafana dashboards populated
- [ ] Alerts configured and tested
- [ ] Logs aggregating properly
- [ ] Traces appearing in Jaeger
- [ ] Database backups automated
- [ ] Load tests passing
- [ ] Health checks succeeding
- [ ] Latency within SLOs
- [ ] Error rates within SLOs
- [ ] Memory/CPU usage normal
- [ ] Network policies working
- [ ] mTLS certificates installed
- [ ] Documentation updated

## Troubleshooting

### Pods not starting

```bash
# Check events
kubectl describe pod <pod-name> -n fintech-services

# Check logs
kubectl logs <pod-name> -n fintech-services

# Check resource availability
kubectl describe nodes
```

### Services not discovering each other

```bash
# Test DNS resolution
kubectl exec -it <pod> -n fintech-services -- \
  nslookup auth-service.fintech-services.svc.cluster.local

# Check service endpoints
kubectl get endpoints -n fintech-services
```

### Metrics not appearing

```bash
# Check Prometheus scrape status
kubectl exec -it prometheus-0 -n fintech-services -- \
  curl http://localhost:9090/api/v1/targets

# Check service metrics endpoint
kubectl exec -it auth-service-0 -n fintech-services -- \
  curl http://localhost:8001/metrics | head -20
```

## Maintenance

### Scaling

```bash
# Manual scale
kubectl scale deployment auth-service --replicas=5 -n fintech-services

# Or update HPA
kubectl patch hpa auth-service-hpa -n fintech-services -p \
  '{"spec":{"minReplicas":3,"maxReplicas":20}}'
```

### Upgrades

```bash
# Update image
kubectl set image deployment/auth-service \
  auth-service=fintech-services/auth-service:v1.0.1 \
  -n fintech-services

# Monitor rollout
kubectl rollout status deployment/auth-service -n fintech-services
```

### Rollback

```bash
# Immediate rollback
kubectl rollout undo deployment/auth-service -n fintech-services

# Rollback to specific revision
kubectl rollout undo deployment/auth-service \
  --to-revision=2 \
  -n fintech-services
```

## Support & Documentation

- Operational Runbooks: `docs/OPERATIONAL_RUNBOOKS.md`
- Incident Response: `docs/INCIDENT_RESPONSE.md`
- SLO/SLI Guide: `docs/SLO_SLI_GUIDE.md`
- Architecture: `MICROSERVICES_ARCHITECTURE.md`

