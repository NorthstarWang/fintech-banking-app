# Incident Response Procedures

Production incident response playbook for FinTech microservices.

## Incident Classification

### Severity Levels

| Severity | Impact | Response Time | Example |
|----------|--------|----------------|---------|
| **SEV-1** | Critical | 15 min | Complete service outage, data loss |
| **SEV-2** | High | 1 hour | Partial outage, significant degradation |
| **SEV-3** | Medium | 4 hours | Feature unavailable, performance issues |
| **SEV-4** | Low | 24 hours | Minor bugs, cosmetic issues |

---

## SEV-1: Critical Outage

**Triggered when**: Complete service unavailable, data loss, security breach

### Immediate Actions (First 15 minutes)

```
1. ENGAGE: Page on-call engineer & manager
   - Slack: @oncall-engineer @engineering-manager
   - PagerDuty: Trigger SEV-1 incident

2. ASSESS:
   - Check if this is a real incident or alert misconfiguration
   - Identify affected services/users
   - Estimate user impact

3. DECLARE: Create incident war room
   - Zoom link: https://zoom.us/incident
   - Slack channel: #sev1-incident
   - Incident ID: YYYY-MM-DD-HHmm-[service]

4. COMMUNICATE:
   - Update status page (https://status.fintech.com)
   - Notify affected customers
   - Create incident post in Slack
```

### Incident War Room

**Participants**:
- Incident Commander (IC) - Leads response
- Technical Lead - Deep diagnostics
- Communications Lead - Updates stakeholders
- Database Administrator - If DB involved
- On-call Engineer(s) - Implementation

**Communication Template**:

```
[Incident War Room]
Incident: [Name]
ID: [ID]
Status: ACTIVE
Severity: SEV-1 - CRITICAL

Impact: [Services affected], [User count], [Data affected]
Root Cause: [Current hypothesis]
Actions in Progress:
1. [Action by person]
2. [Action by person]

ETA to Resolution: [Time estimate]
Last Update: [Timestamp]
```

### Diagnosis Steps

```bash
# 1. Check service status
kubectl get pods -n fintech-services

# 2. Check logs for errors
kubectl logs -n fintech-services --all-containers=true \
  --timestamps=true | grep -i "error\|exception\|panic" | tail -100

# 3. Check metrics
# Prometheus: http://localhost:9090
# Look for: error rate, latency, pod restarts

# 4. Check database connectivity
kubectl exec -it auth-service-xxxx -n fintech-services -- \
  psql $DATABASE_URL -c "SELECT 1"

# 5. Check dependencies
curl -s http://auth-service:8001/health | jq
curl -s http://notification-service:8002/health | jq
```

### Recovery Actions

**For Database Failure**:
```bash
# 1. Check database pod
kubectl get pods -n fintech-services -l app=postgres

# 2. Check PVC
kubectl get pvc -n fintech-services

# 3. If database pod is down, scale it up
kubectl scale statefulset postgres --replicas=1 -n fintech-services

# 4. Wait for recovery and verify
kubectl wait --for=condition=Ready pod -l app=postgres \
  -n fintech-services --timeout=5m

# 5. Verify data integrity
kubectl exec -it postgres-0 -n fintech-services -- \
  psql $DATABASE_URL -c "SELECT count(*) FROM transactions"
```

**For Service Cascade Failure**:
```bash
# 1. Identify failing service from logs
# 2. Isolate it
kubectl scale deployment failing-service --replicas=0 -n fintech-services

# 3. Reset circuit breakers
kubectl exec -it auth-service-xxxx -n fintech-services -- \
  curl -X POST http://localhost:8001/circuit-breakers/reset

# 4. Restart dependent services
kubectl rollout restart deployment/account-service -n fintech-services

# 5. Scale failing service back up once fixed
kubectl scale deployment failing-service --replicas=2 -n fintech-services
```

**For Memory/Resource Exhaustion**:
```bash
# 1. Identify pod
kubectl top pods -n fintech-services --sort-by=memory

# 2. Check logs for memory leak patterns
kubectl logs pod-name -n fintech-services | tail -500

# 3. Restart pod
kubectl delete pod pod-name -n fintech-services

# 4. Monitor for recurrence
kubectl top pod pod-name -n fintech-services --containers -w
```

### Resolution Verification

```bash
# 1. Verify service health
for svc in auth-service notification-service analytics-service; do
  kubectl exec -it $(kubectl get pods -n fintech-services \
    -l app=$svc -o jsonpath='{.items[0].metadata.name}') \
    -n fintech-services -- curl http://localhost:8001/health
done

# 2. Check error rates normalized
# Prometheus: rate(http_requests_total{status="5xx"}[5m]) < 0.01

# 3. Check latency normalized
# Prometheus: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) < 1

# 4. Test functionality
# Run smoke tests / synthetic monitoring
```

### Post-Incident

```
1. Update status page: RESOLVED
2. Send all-clear message to customers
3. Document timeline in war room
4. Schedule post-mortem within 24 hours
5. Create follow-up tasks for prevention
6. Update runbooks if needed
```

---

## SEV-2: High Impact Partial Outage

**Triggered when**: One service down, partial degradation, ~25% users affected

### Response Protocol (1 hour SLA)

```
T+0 min: Page on-call engineer
         Assess scope and impact

T+5 min: Declare incident
         Create war room (smaller than SEV-1)
         Update status page

T+15 min: Diagnosis complete
          Root cause identified

T+30 min: Mitigation in progress

T+60 min: Resolution or escalation to SEV-1
```

### Common SEV-2 Scenarios

**Single service down** (e.g., Notification Service):
```bash
# 1. Check service status
kubectl get pods -n fintech-services -l app=notification-service

# 2. Check logs
kubectl logs -n fintech-services -l app=notification-service --tail=200

# 3. If misconfiguration
kubectl rollout restart deployment/notification-service -n fintech-services

# 4. If bug, deploy fix
kubectl set image deployment/notification-service \
  notification-service=fintech-services/notification-service:vX.X.X \
  -n fintech-services

# 5. Monitor recovery
kubectl rollout status deployment/notification-service -n fintech-services
```

**High error rate** (but service responding):
```bash
# 1. Identify which endpoint has errors
# Prometheus: rate(http_requests_total{status="5xx"}[5m])

# 2. Check service logs for specific errors
kubectl logs -n fintech-services <pod> | grep -i error | tail -50

# 3. Check dependencies (database, external APIs)

# 4. If database issue: scale DB resources or add read replicas

# 5. If external API: enable fallback or cache

# 6. If code bug: deploy hotfix
```

---

## SEV-3: Medium Impact Issues

**Triggered when**: Specific feature down, performance degradation, <5% users affected

### Checklist

- [ ] Create incident ticket
- [ ] Assign to engineer
- [ ] Update progress every 30 minutes
- [ ] Target resolution within 4 hours

### Investigation

```bash
# 1. Identify affected service/feature
# 2. Reproduce issue locally if possible
# 3. Check logs and metrics
# 4. Propose fix
# 5. Test before deployment
# 6. Deploy during maintenance window if non-critical
```

---

## SEV-4: Low Priority Issues

**Triggered when**: Minor bugs, cosmetic issues, workarounds available

### Process

- File JIRA ticket
- Add to sprint backlog
- Resolve in next release cycle
- No immediate action required

---

## Post-Incident Process

### Incident Post-Mortem (Within 24 hours)

**Template**:

```markdown
# Incident Post-Mortem

**Incident**: [Name]
**Date**: [Date]
**Duration**: [HH:mm]
**Severity**: SEV-[1-4]

## Summary
[Brief description of what happened]

## Impact
- Affected Services: [List]
- Affected Users: [Estimate]
- Data Loss: [Yes/No]
- Financial Impact: $[Estimate]

## Timeline
- T+0: [What happened]
- T+5: [First response]
- T+15: [Root cause identified]
- T+30: [Mitigation started]
- T+60: [Resolved]

## Root Cause
[Description of root cause]

## Contributing Factors
1. [Factor 1]
2. [Factor 2]

## Lessons Learned
1. [What we learned]
2. [What we'll improve]

## Action Items
- [ ] [Action] - Owner: [Name] - Due: [Date]
- [ ] [Action] - Owner: [Name] - Due: [Date]
```

### Action Item Tracking

```bash
# Create JIRA tickets for action items
jira issue create \
  --project FINTECH \
  --type Task \
  --summary "Incident Follow-up: Improve [X]" \
  --description "Post-mortem action from incident [ID]" \
  --assignee engineer@company.com \
  --duedate 2024-01-22
```

### Error Budget Tracking

Monitor error budgets post-incident:

```
SLO: 99.95% uptime
Error Budget: 0.05% = ~2 minutes/month

If incident caused 0.1% downtime, consumed 2 months of budget
Plan accordingly for deployment windows
```

---

## Escalation Matrix

### Escalation Path

```
L1: On-call Engineer (15 min response)
    ├─ Attempt diagnosis and mitigation
    ├─ If stuck > 15 min or unclear impact → Escalate

L2: Engineering Manager (5 min response)
    ├─ Technical oversight
    ├─ Resource coordination
    ├─ If stuck > 30 min → Escalate

L3: VP Engineering (On-demand)
    ├─ Strategic decisions
    ├─ Customer escalations
    ├─ PR/external communication
```

### When to Escalate

- Technical solution unclear
- Multiple services affected
- Potential data loss
- Customer escalation
- SEV-1 classification
- Approaching SLA limits

---

## Communication Templates

### For Customers

**Initial**: "We're investigating an issue affecting [service]. We'll provide updates every 15 minutes."

**Update**: "We've identified the root cause. We're implementing a fix, estimated [time]."

**Resolution**: "Issue resolved. Affected users may need to refresh. We apologize for the inconvenience."

### For Internal Team

**In Slack**:
```
🚨 SEV-2 INCIDENT: Auth Service Down
- Affected: Login functionality (~30% users)
- Start: 2024-01-15 14:23 UTC
- Status: INVESTIGATING
- ETA: 15:00 UTC
- War Room: https://zoom.us/incident
```

---

## Tools & Resources

- **Status Page**: https://status.fintech.com (update here first)
- **War Room**: https://zoom.us/incident
- **Incident Slack**: #incidents
- **On-Call**: PagerDuty (link)
- **Monitoring**:
  - Prometheus: http://prometheus:9090
  - Grafana: http://grafana:3000
  - Jaeger: http://jaeger:16686

---

## Testing & Drills

### Monthly Incident Drill

```
1. Simulate outage (disable service)
2. Measure detection time
3. Measure response time
4. Measure resolution time
5. Collect feedback
6. Update runbooks
```

### Chaos Engineering Tests

```bash
# Kill random pod
kubectl delete pod $(kubectl get pods -n fintech-services -o name | shuf -n 1)

# Simulate high latency
kubectl exec -it <pod> -- tc qdisc add dev eth0 root netem delay 1000ms

# Simulate packet loss
kubectl exec -it <pod> -- tc qdisc add dev eth0 root netem loss 5%

# Monitor system behavior and recovery
```

