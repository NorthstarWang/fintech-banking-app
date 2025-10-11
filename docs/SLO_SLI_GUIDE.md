# SLO & SLI Framework

Service Level Objectives (SLOs) and Indicators (SLIs) for FinTech microservices.

## Service Level Definitions

### Service Level Indicator (SLI)

A metric that measures compliance with the SLO.

**Examples**:
- % of requests with latency < 100ms
- % of requests that return status 2xx
- % of data delivered within SLA

### Service Level Objective (SLO)

A target value or range for an SLI over a period of time.

**Examples**:
- 99.95% of requests should complete within 200ms
- 99.99% of requests should succeed

### Service Level Agreement (SLA)

A commitment to customers, often with penalties for breach.

**Examples**:
- 99.9% uptime (up to 43 minutes downtime/month)
- 10% refund if SLO breached

---

## FinTech Microservices SLOs

### Availability SLO

| Service | SLO | Error Budget |
|---------|-----|--------------|
| API Gateway | 99.95% | 2.16 min/day |
| Auth Service | 99.99% | 0.43 min/day |
| Transaction Service | 99.99% | 0.43 min/day |
| Payment Service | 99.95% | 2.16 min/day |
| Account Service | 99.99% | 0.43 min/day |
| Analytics Service | 99% | 14.4 min/day |

### Latency SLO (P95)

| Service | Latency | Notes |
|---------|---------|-------|
| API Gateway | 200ms | Includes downstream |
| Auth Service | 100ms | Cached tokens |
| Transaction Service | 150ms | Including DB |
| Payment Service | 500ms | External API dependency |
| Account Service | 100ms | Simple query |
| Analytics Service | 1000ms | Computation intensive |

### Error Rate SLO

| Service | Target | Alert Threshold |
|---------|--------|-----------------|
| API Gateway | <0.1% | >0.2% |
| Auth Service | <0.01% | >0.05% |
| Transaction Service | <0.01% | >0.05% |
| Payment Service | <0.1% | >0.2% |
| Account Service | <0.01% | >0.05% |

---

## Key SLIs

### Availability

**Definition**: % of successful requests over time period

```promql
# Calculate SLI for API Gateway
sum(rate(http_requests_total{job="api-gateway",status="2xx"}[5m])) /
sum(rate(http_requests_total{job="api-gateway"}[5m]))

# Alert on SLO breach
(
  sum(rate(http_requests_total{job="api-gateway",status!="2xx"}[5m])) /
  sum(rate(http_requests_total{job="api-gateway"}[5m]))
) > 0.0005
```

### Latency

**Definition**: P95 request duration

```promql
# Calculate P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Alert on SLO breach
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.2
```

### Error Rate

**Definition**: % of requests returning 5xx status

```promql
# Calculate error rate
sum(rate(http_requests_total{status="5xx"}[5m])) /
sum(rate(http_requests_total[5m]))

# Alert on SLO breach
(
  sum(rate(http_requests_total{status="5xx"}[5m])) /
  sum(rate(http_requests_total[5m]))
) > 0.001
```

### Saturation

**Definition**: How full/busy a service is

```promql
# CPU saturation
rate(container_cpu_usage_seconds_total{pod=~".*-service.*"}[5m]) /
container_spec_cpu_quota{pod=~".*-service.*"}

# Memory saturation
container_memory_usage_bytes{pod=~".*-service.*"} /
container_spec_memory_limit_bytes{pod=~".*-service.*"}

# Database connection saturation
pg_stat_activity_count / max_connections
```

---

## Error Budget

The amount of downtime or errors allowed while still meeting SLO.

### Calculation

```
Error Budget = (1 - SLO) × Time Period

Example:
SLO: 99.95% (0.05% allowed errors)
Period: 30 days = 43,200 minutes

Error Budget = 0.0005 × 43,200 = 21.6 minutes/month
```

### Error Budget Remaining

```promql
# Remaining error budget for month
(1 - (1 - SLO)) * days_in_month * minutes_per_day - consumed_downtime
```

### Error Budget Depletion Policy

1. **Healthy** (>50% budget remaining)
   - Deploy changes during business hours
   - Regular maintenance allowed

2. **Warning** (10-50% budget remaining)
   - Deploy only critical hotfixes
   - Reduce change velocity
   - Increase testing

3. **Critical** (<10% budget remaining)
   - Freeze all changes except emergencies
   - Focus on stability
   - Defer features to next period

---

## SLI Tracking Dashboard

### Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "SLO/SLI Tracking",
    "panels": [
      {
        "title": "Monthly Uptime by Service",
        "type": "graph",
        "targets": [
          {
            "expr": "sum by (job) (rate(http_requests_total{status=\"2xx\"}[5m])) / sum by (job) (rate(http_requests_total[5m]))"
          }
        ]
      },
      {
        "title": "P95 Latency Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Budget Burn Down",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(http_requests_total{status=\"5xx\"}[30d])"
          }
        ]
      },
      {
        "title": "Circuit Breaker State",
        "type": "stat",
        "targets": [
          {
            "expr": "circuit_breaker_state"
          }
        ]
      }
    ]
  }
}
```

---

## Alert Rules

### Prometheus Alert Rules

```yaml
groups:
  - name: slo_alerts
    rules:
      # Availability SLO alerts
      - alert: AvailabilitySLOBreach
        expr: |
          (sum(rate(http_requests_total{status="5xx"}[5m])) /
           sum(rate(http_requests_total[5m]))) > 0.001
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.job }} availability SLO breached"

      # Latency SLO alerts
      - alert: LatencySLOBreach
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.job }} latency SLO breached"

      # Error budget depletion
      - alert: ErrorBudgetDepleted
        expr: |
          (increase(http_requests_total{status="5xx"}[30d]) /
           increase(http_requests_total[30d])) > (1 - 0.9995)
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.job }} error budget depleted"
```

---

## Monthly Review Process

### SLO Review Meeting (First Monday of month)

**Attendees**: Engineering Manager, Tech Lead, On-call engineer

**Agenda**:
1. Review previous month SLO compliance
2. Identify SLOs breached and root causes
3. Review action items from breaches
4. Discuss needed adjustments
5. Plan for next month

**Template**:

```markdown
# SLO Review - January 2024

## Summary
- API Gateway: 99.96% (SLO: 99.95%) ✓ PASS
- Auth Service: 99.98% (SLO: 99.99%) ✗ MISS
- Transaction Service: 99.99% (SLO: 99.99%) ✓ PASS
- Payment Service: 99.93% (SLO: 99.95%) ✗ MISS
- Account Service: 99.99% (SLO: 99.99%) ✓ PASS
- Analytics Service: 99.2% (SLO: 99%) ✓ PASS

## SLO Breaches
### Auth Service (Missed by 0.01%)
- Incident: Database connection pool exhaustion on Jan 15
- Root Cause: Spike in password reset requests
- Action: Increase connection pool from 20 to 50
- Status: COMPLETED

### Payment Service (Missed by 0.02%)
- Incident: External payment API timeout on Jan 20-22
- Root Cause: Stripe API outage + our retry logic causing cascades
- Action: Implement circuit breaker + fallback queue
- Status: IN PROGRESS

## Error Budget Utilization
- Auth Service: Used 95% of budget (0.8 of 1 minute)
- Payment Service: Used 87% of budget (1.88 of 2.16 minutes)
- Others: <50% utilization

## Recommendations
1. Increase alerting sensitivity for Auth Service
2. Complete Payment Service circuit breaker implementation
3. Schedule load testing for peak capacity
4. Review SLO targets with Product team
```

---

## SLO Adjustments

### When to Adjust SLOs

1. **Tighten SLO** if:
   - Consistently exceeding SLO targets
   - User feedback indicates need for higher reliability
   - Competitive advantage from higher reliability

2. **Relax SLO** if:
   - Consistently missing SLO despite efforts
   - Infrastructure limitations make target unrealistic
   - Cost/benefit ratio unfavorable

### SLO Adjustment Process

1. Technical Lead proposes new SLO
2. Engineering Manager reviews feasibility
3. Product/Business stakeholders approve
4. Update Prometheus alert rules
5. Update dashboard and tracking
6. Announce to team

---

## Reporting

### Daily SLO Report

```bash
#!/bin/bash
# Sent to #engineering-daily channel

echo "=== SLO Status (Last 24h) ==="
echo "API Gateway: $(query_sli 'api-gateway' 24h)% (Target: 99.95%)"
echo "Auth Service: $(query_sli 'auth-service' 24h)% (Target: 99.99%)"
echo "Payment Service: $(query_sli 'payment-service' 24h)% (Target: 99.95%)"
echo ""
echo "Error Budget Remaining (30-day):"
echo "Auth Service: $(error_budget 'auth-service' 30d)%"
echo "Payment Service: $(error_budget 'payment-service' 30d)%"
```

### Weekly SLO Report

- Service-by-service SLO compliance
- Trend analysis (improving/degrading)
- Alert analysis (false positives/negatives)
- Action item status

### Monthly SLO Report

- Full SLO compliance review
- Root cause analysis for breaches
- Error budget utilization
- Recommendations for next month
- SLO target review

---

## Tools & Integration

### Prometheus Queries

```promql
# Monthly uptime percentage
(sum(increase(http_requests_total{status="2xx"}[30d])) /
 sum(increase(http_requests_total[30d]))) * 100

# Services below SLO
(sum by (job) (rate(http_requests_total{status="5xx"}[5m])) /
 sum by (job) (rate(http_requests_total[5m]))) > 0.0005

# Error budget consumption rate
sum(rate(http_requests_total{status="5xx"}[1h])) /
sum(rate(http_requests_total[1h]))
```

### Integration Points

- Prometheus: Metric collection
- Grafana: Visualization
- AlertManager: Alert routing
- PagerDuty: On-call escalation
- JIRA: Incident tracking
- Slack: Team notifications

