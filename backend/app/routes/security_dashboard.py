"""
Security operations dashboard endpoints.

Provides real-time monitoring of authentication, transactions, and API security.
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import User
from ..security.anomaly_detection import AnomalyDetector, LoginAttempt, TransactionAnomaly
from ..security.audit_logging import AuditLogger
from ..security.security_responses import SecurityIncident, SecurityResponses
from ..storage.memory_adapter import db as memory_db

router = APIRouter(prefix="/api/admin/security", tags=["security_dashboard"])


def get_current_admin(db: Session = Depends(lambda: memory_db)) -> User:
    """Verify admin access."""
    # In production, implement proper admin authentication
    return None


@router.get("/dashboard/auth")
async def get_auth_monitoring(
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Get authentication monitoring data."""
    # Get recent login attempts
    recent_logins = db.query(LoginAttempt).filter(
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(hours=1)
    ).order_by(LoginAttempt.timestamp.desc()).limit(50).all()

    # Get failed login attempts grouped by user
    failed_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.success == 0,
        LoginAttempt.timestamp > datetime.utcnow() - timedelta(hours=4),
    ).all()

    # Group failed attempts by user
    failed_by_user = {}
    locked_accounts = []

    for attempt in failed_attempts:
        if attempt.user_id not in failed_by_user:
            failed_by_user[attempt.user_id] = 0
        failed_by_user[attempt.user_id] += 1

        if failed_by_user[attempt.user_id] >= AnomalyDetector.FAILED_LOGIN_THRESHOLD:
            if attempt.user_id not in locked_accounts:
                locked_accounts.append(attempt.user_id)

    return {
        "recent_logins": [
            {
                "user_id": login.user_id,
                "ip_address": login.ip_address,
                "location": login.location,
                "timestamp": login.timestamp.isoformat(),
                "risk_score": login.risk_score,
                "success": login.success == 1,
            }
            for login in recent_logins
        ],
        "failed_login_summary": failed_by_user,
        "locked_accounts": locked_accounts,
        "lockout_threshold": AnomalyDetector.FAILED_LOGIN_THRESHOLD,
    }


@router.get("/dashboard/transactions")
async def get_transaction_security(
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Get transaction security monitoring data."""
    # Get high-risk transactions
    high_risk = db.query(TransactionAnomaly).filter(
        TransactionAnomaly.risk_score > 0.6,
        TransactionAnomaly.timestamp > datetime.utcnow() - timedelta(hours=24),
    ).order_by(TransactionAnomaly.risk_score.desc()).limit(20).all()

    # Get flagged transactions
    flagged = db.query(TransactionAnomaly).filter(
        TransactionAnomaly.flagged == 1,
        TransactionAnomaly.timestamp > datetime.utcnow() - timedelta(hours=24),
    ).all()

    # Calculate statistics
    total_analyzed = db.query(TransactionAnomaly).filter(
        TransactionAnomaly.timestamp > datetime.utcnow() - timedelta(hours=24),
    ).count()

    return {
        "high_risk_transactions": [
            {
                "transaction_id": t.transaction_id,
                "user_id": t.user_id,
                "amount": t.amount,
                "anomaly_type": t.anomaly_type,
                "risk_score": t.risk_score,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in high_risk
        ],
        "flagged_transactions": len(flagged),
        "total_analyzed": total_analyzed,
        "risk_threshold": 0.6,
    }


@router.get("/dashboard/api-security")
async def get_api_security(
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Get API security metrics."""
    # This would typically query rate limiting and auth logs
    return {
        "rate_limit_violations": 0,
        "failed_auth_attempts": 0,
        "invalid_token_patterns": [],
        "api_endpoints_monitored": [
            "/api/transfers",
            "/api/transactions/new",
            "/api/accounts/create",
        ],
    }


@router.get("/incidents")
async def get_security_incidents(
    status_filter: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Get security incidents."""
    query = db.query(SecurityIncident)

    if status_filter:
        query = query.filter(SecurityIncident.status == status_filter)

    if severity:
        query = query.filter(SecurityIncident.severity == severity)

    incidents = query.order_by(
        SecurityIncident.created_at.desc()
    ).limit(limit).all()

    return {
        "incidents": [
            {
                "id": inc.id,
                "user_id": inc.user_id,
                "type": inc.incident_type,
                "severity": inc.severity,
                "status": inc.status,
                "created_at": inc.created_at.isoformat(),
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            }
            for inc in incidents
        ],
        "total": len(incidents),
    }


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    resolution: str,
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Resolve a security incident."""
    incident = SecurityResponses.resolve_incident(db, incident_id, resolution)

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return {
        "id": incident.id,
        "status": incident.status,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
    }


@router.post("/accounts/{user_id}/unlock")
async def unlock_account(
    user_id: int,
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, str]:
    """Manually unlock a locked account."""
    from ..security.security_responses import AccountLockout

    lockout = db.query(AccountLockout).filter(
        AccountLockout.user_id == user_id
    ).first()

    if lockout:
        db.delete(lockout)
        db.commit()

    return {"message": "Account unlocked", "user_id": user_id}


@router.get("/audit-logs")
async def get_audit_logs(
    user_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Get audit logs for security review."""
    if user_id:
        logs = AuditLogger.get_user_audit_log(db, user_id, limit)
    else:
        logs = db.query(AuditLogger.__bases__[0]).order_by(
            "timestamp"
        ).limit(limit).all()

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ],
        "total": len(logs),
    }


@router.post("/audit-logs/verify-chain")
async def verify_audit_chain(
    db: Session = Depends(lambda: memory_db),
    _admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Verify audit log chain integrity."""
    is_intact, broken_hashes = AuditLogger.verify_chain_integrity(db)

    return {
        "chain_intact": is_intact,
        "broken_entries": len(broken_hashes),
        "tamper_detected": len(broken_hashes) > 0,
        "broken_hashes": broken_hashes[:10] if broken_hashes else [],
    }
