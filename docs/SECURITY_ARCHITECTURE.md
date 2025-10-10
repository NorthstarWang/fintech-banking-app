# Investment Trading Platform - Security Architecture

Enterprise-grade zero-trust security implementation for production deployment.

## Table of Contents

1. [Overview](#overview)
2. [Device Fingerprinting & Trust Management](#device-fingerprinting--trust-management)
3. [Anomaly Detection](#anomaly-detection)
4. [Request Signing & Integrity](#request-signing--integrity)
5. [Field-Level Encryption](#field-level-encryption)
6. [Audit Logging](#audit-logging)
7. [Automated Security Responses](#automated-security-responses)
8. [Security Dashboard](#security-dashboard)
9. [Incident Response](#incident-response)

---

## Overview

This platform implements multiple layers of security controls:

- **Zero-Trust Architecture**: Verify every request, every time
- **Device Fingerprinting**: Track and validate device identity
- **Anomaly Detection**: Real-time pattern analysis for suspicious activity
- **Cryptographic Controls**: Request signing and field-level encryption
- **Tamper-Resistant Logging**: Audit trail with integrity verification
- **Automated Responses**: Immediate threat mitigation without manual intervention

---

## Device Fingerprinting & Trust Management

### Purpose
Capture device signatures and manage trusted devices per user. Require additional verification for new/unknown devices.

### Components

**Device Fingerprinting Attributes:**
- Browser fingerprint (canvas, WebGL, plugins)
- Screen resolution
- Timezone
- Plugins/extensions
- IP address
- User agent

**Trusted Device Storage:**
```
TrustedDevice
├── user_id
├── device_fingerprint (SHA256 hash)
├── device_name
├── device_info (JSON)
├── browser_fingerprint
├── screen_resolution
├── timezone
├── is_trusted (boolean)
├── last_seen (timestamp)
├── created_at (timestamp)
└── ip_address
```

### API Usage

**Generate Device Fingerprint:**
```python
from app.security.device_fingerprint import DeviceFingerprint

fingerprint = DeviceFingerprint.generate_fingerprint(
    user_agent="Mozilla/5.0...",
    ip_address="192.168.1.1",
    browser_data={
        "screen_resolution": "1920x1080",
        "timezone": "America/New_York",
        "plugins": ["plugin1", "plugin2"]
    }
)
```

**Get or Create Device:**
```python
device = DeviceFingerprint.get_or_create_device(
    db=session,
    user_id=123,
    fingerprint=fingerprint,
    device_info=device_data,
    ip_address="192.168.1.1"
)
```

**Mark Device as Trusted:**
```python
DeviceFingerprint.mark_device_trusted(db=session, device_id=device.id)
```

### Device Change Detection

The system detects changes that might indicate account compromise:
- Screen resolution changes
- Timezone changes
- Browser fingerprint changes
- Operating system changes

---

## Anomaly Detection

### Purpose
Monitor login patterns and transactions to detect suspicious behavior. Score risk for adaptive authentication.

### Login Anomaly Detection

**Monitored Patterns:**
- Time of day (unusual hours: 2 AM - 5 AM)
- Location changes
- Impossible travel (different continents within hours)
- Failed login frequency

**Risk Scoring:**
- Unusual time: +0.2
- Location change: +0.3
- Impossible travel: +0.8
- Multiple failed attempts: +0.5

**Thresholds:**
- MFA required: Risk score > 0.5
- Additional verification: Risk score > 0.7
- Account locked: 5+ failed attempts in 30 minutes

### Transaction Anomaly Detection

**Monitored Patterns:**
- Unusual amounts (>2x average for category)
- High velocity (>5 transactions/hour)
- Unusual categories
- Geographic anomalies

**Risk Scoring:**
- Unusual amount: +0.3
- High velocity: +0.4
- Unusual category: +0.2

**Actions:**
- Review required: Risk score > 0.5
- Quarantine: Risk score > 0.7

### Data Models

```python
LoginAttempt
├── user_id
├── ip_address
├── timestamp
├── success (0/1)
├── location
├── device_fingerprint
└── risk_score

TransactionAnomaly
├── user_id
├── transaction_id
├── amount
├── timestamp
├── anomaly_type (amount, velocity, category, location)
├── risk_score
└── flagged
```

---

## Request Signing & Integrity

### Purpose
Prevent replay attacks and ensure integrity of financial operations.

### Implementation

**HMAC-SHA256 Signing:**
1. Create payload: `METHOD\nENDPOINT\nBODY\nTIMESTAMP\nNONCE`
2. Sign with secret key: `HMAC-SHA256(payload, secret_key)`
3. Include signature, timestamp, nonce in request headers

**Headers:**
```
X-Signature: <signature>
X-Timestamp: <unix_timestamp>
X-Nonce: <unique_uuid>
X-Algorithm: sha256
```

**Validation:**
- Timestamp within 5 minutes
- Signature verification (constant-time comparison)
- Nonce verification (prevent replay)

### API Usage

**Generate Signature:**
```python
from app.security.request_signing import RequestSignature

sig_data = RequestSignature.generate_signature(
    method="POST",
    endpoint="/api/transfers",
    body={"amount": 1000, "to_account": 456},
    timestamp=int(time.time()),
    nonce=str(uuid.uuid4())
)
```

**Verify Signature:**
```python
is_valid, message = RequestSignature.verify_signature(
    method=request.method,
    endpoint=request.url.path,
    signature=request.headers.get("X-Signature"),
    timestamp=request.headers.get("X-Timestamp"),
    nonce=request.headers.get("X-Nonce"),
    body=await request.json()
)
```

---

## Field-Level Encryption

### Purpose
Protect PII like SSNs, account numbers, and tax IDs.

### Implementation

**Algorithm:** Fernet (AES-128 with HMAC) over derived key
**Key Derivation:** PBKDF2(secret_key, salt, 100,000 iterations)

**Encrypted Fields:**
- SSN (format: XXX-XX-XXXX)
- Account numbers
- Tax IDs (EIN, ITIN)
- Sensitive personally identifiable information

### API Usage

**Encrypt SSN:**
```python
from app.security.field_encryption import FieldEncryption

encrypted_ssn = FieldEncryption.encrypt_ssn("123-45-6789")
```

**Decrypt SSN:**
```python
ssn = FieldEncryption.decrypt_ssn(encrypted_ssn)
```

**Mask SSN (Display):**
```python
masked = FieldEncryption.mask_ssn("123-45-6789")  # Returns: ***-**-6789
```

**Batch Encrypt Dictionary:**
```python
encrypted_data = FieldEncryption.encrypt_dict(
    data=user_data,
    fields_to_encrypt=["ssn", "account_number", "tax_id"]
)
```

---

## Audit Logging

### Purpose
Tamper-resistant logging with cryptographic chaining for compliance.

### Implementation

**Cryptographic Chaining:**
1. Calculate hash of current log: `SHA256(log_data + previous_hash)`
2. Store previous hash in current log
3. Chain creates immutable sequence

**Log Entry Structure:**
```
AuditLog
├── id
├── user_id
├── action (CREATE, UPDATE, DELETE, READ, TRANSFER)
├── resource_type (Account, Transaction, User)
├── resource_id
├── timestamp
├── details (JSON)
├── ip_address
├── user_agent
├── previous_hash (chain link)
├── current_hash (integrity)
└── encrypted
```

### Logged Actions

**Authentication Events:**
- Login attempt (success/failure)
- MFA verification
- Session creation/termination

**Data Access:**
- Read access to PII
- Document downloads
- Data exports

**Modifications:**
- Account creation/updates
- Transaction creation
- Profile changes

**Security Events:**
- Failed authentication
- Lockouts
- Suspicious activities
- Incident creation

### API Usage

**Log Action:**
```python
from app.security.audit_logging import AuditLogger

log = AuditLogger.log_action(
    db=session,
    user_id=123,
    action="TRANSFER",
    resource_type="Transaction",
    resource_id=789,
    details={"amount": 1000, "to_account": 456},
    ip_address="192.168.1.1"
)
```

**Log Data Access:**
```python
AuditLogger.log_data_access(
    db=session,
    user_id=123,
    resource_type="User",
    resource_id=123,
    fields_accessed=["ssn", "account_number"],
    ip_address="192.168.1.1"
)
```

**Verify Chain Integrity:**
```python
is_intact, broken_hashes = AuditLogger.verify_chain_integrity(db=session)
if not is_intact:
    # Alert: Tampering detected
    SecurityResponses.create_incident(
        db=session,
        user_id=0,
        incident_type="AUDIT_LOG_TAMPER",
        severity="critical"
    )
```

---

## Automated Security Responses

### Purpose
Protect system without manual intervention.

### Response Types

**1. Account Lockout**
- Trigger: 5+ failed login attempts in 15 minutes
- Action: Lock account for 15 minutes
- Notification: Email alert to user
- Override: Admin unlock or auto-unlock after 15 minutes

**2. Step-Up Authentication**
- Trigger: Transaction > $10,000
- Action: Require additional MFA
- Options: SMS code, authenticator app, security questions

**3. Transaction Quarantine**
- Trigger: Risk score > 0.7
- Action: Hold transaction pending review
- Timeframe: 24-hour manual review window
- Override: Admin approval

**4. Account Restrictions**
- Trigger: Multiple compromise indicators
- Action: Restrict account pending investigation
- Notification: Immediate email/SMS alert
- Recovery: Admin investigation and approval

**5. Security Incidents**
- Automatic creation for:
  - Excessive failed logins
  - High-risk transactions
  - Device changes
  - Impossible travel
  - Audit log tampering

### API Usage

**Handle Failed Login:**
```python
from app.security.security_responses import SecurityResponses

result = SecurityResponses.handle_failed_login(
    db=session,
    user_id=123,
    ip_address="192.168.1.1",
    attempt_count=5
)

if result["blocked"]:
    # Account locked, return 429 Too Many Requests
    pass
```

**Handle High-Risk Transaction:**
```python
result = SecurityResponses.handle_high_risk_transaction(
    db=session,
    user_id=123,
    transaction_id=789,
    amount=15000,
    risk_score=0.75
)

if result["quarantine"]:
    # Hold transaction, notify admin
    pass
```

---

## Security Dashboard

### Endpoint: `/api/admin/security`

**Available Endpoints:**

1. **Authentication Monitoring**
   ```
   GET /dashboard/auth
   Returns:
   - Recent login attempts
   - Failed login summary by user
   - Locked accounts
   - Lockout threshold
   ```

2. **Transaction Security**
   ```
   GET /dashboard/transactions
   Returns:
   - High-risk transactions (risk > 0.6)
   - Flagged transactions
   - Transaction statistics
   ```

3. **API Security**
   ```
   GET /dashboard/api-security
   Returns:
   - Rate limit violations
   - Failed auth attempts
   - Invalid token patterns
   - Monitored endpoints
   ```

4. **Security Incidents**
   ```
   GET /incidents?status=open&severity=high&limit=50
   Returns:
   - Incident list
   - Incident details
   - Timeline information
   ```

5. **Resolve Incident**
   ```
   POST /incidents/{incident_id}/resolve
   Body: {"resolution": "description"}
   ```

6. **Unlock Account**
   ```
   POST /accounts/{user_id}/unlock
   ```

7. **Audit Logs**
   ```
   GET /audit-logs?user_id=123&limit=100
   POST /audit-logs/verify-chain
   ```

---

## Incident Response

### Severity Levels

- **Critical**: Account compromise, audit tampering, large fraud
- **High**: Multiple failed logins, high-risk transactions, device changes
- **Medium**: Unusual patterns, elevated risk scores
- **Low**: Informational events, audit trail entries

### Response Procedures

**Level 1: Automatic Response**
- Immediate action (lock, quarantine, restrict)
- Email alert to user
- Incident creation for tracking

**Level 2: Admin Review**
- 24-hour review window
- Dashboard notification
- Decision point for approval/denial

**Level 3: Escalation**
- Manual investigation
- Compliance team involvement
- Potential law enforcement notification

### Recovery

**Account Unlock:**
1. Admin verifies identity through secondary channel
2. Review incident details
3. Approve or deny unlock
4. Log admin decision in audit trail

**Transaction Appeal:**
1. User can appeal quarantined transaction
2. Submit supporting documentation
3. Admin review and approval
4. Transaction release or denial

**Account Restoration:**
1. Full investigation by security team
2. Verify no ongoing compromise
3. Reset credentials
4. Enable access
5. Document findings

---

## Security Checklist for Deployment

- [ ] Secret keys configured and rotated
- [ ] Database encryption enabled
- [ ] SSL/TLS certificates installed
- [ ] Rate limiting configured
- [ ] CORS origins restricted
- [ ] Audit logging enabled
- [ ] Admin access restricted to VPN
- [ ] Security dashboard monitored
- [ ] Incident response team trained
- [ ] Backup and recovery plan tested

---

## Compliance

This architecture supports compliance with:
- **OWASP Top 10**: Authentication, cryptography, logging
- **PCI DSS**: Encryption, audit trails, access controls
- **SOC 2**: Monitoring, incident response, audit trails

---

## Contact

For security issues, contact: security@investmentplatform.com

**DO NOT** disclose security vulnerabilities publicly.
