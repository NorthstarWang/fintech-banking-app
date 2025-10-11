"""
Tamper-resistant audit logging with cryptographic chaining.

Creates append-only logs with cryptographic hash chains for tamper detection.
"""
import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

# Import AuditLog from memory models instead of defining SQLAlchemy model
from app.models.memory_models import AuditLog


class AuditLogger:
    """Service for tamper-resistant audit logging."""

    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        event_type: str = "action",
        resource: str | None = None,
    ) -> AuditLog:
        """
        Log an action with cryptographic chaining.

        Args:
            db: Database session
            user_id: ID of user performing action
            action: Action name (CREATE, UPDATE, DELETE, READ, TRANSFER, etc)
            resource_type: Type of resource (Account, Transaction, User, etc)
            resource_id: ID of affected resource
            details: Additional details as dict
            ip_address: Client IP address
            user_agent: Client user agent
            event_type: Type of event (action, security, data_access, etc)
            resource: Resource identifier string (e.g., "transaction:999")

        Returns:
            Created AuditLog entry
        """
        # Get last audit log to chain from
        last_log = db.query(AuditLog).order_by(
            AuditLog.id.desc()
        ).first()

        previous_hash = last_log.current_hash if last_log else ""

        # Create log entry
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
            "ip_address": ip_address,
            "previous_hash": previous_hash,
        }

        # Calculate hash (includes chain)
        current_hash = AuditLogger._calculate_hash(log_data)

        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {}),
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=previous_hash,
            current_hash=current_hash,
            event_type=event_type,
            resource=resource or f"{resource_type}:{resource_id}",
        )

        db.add(audit_log)
        db.commit()

        return audit_log

    @staticmethod
    def log_data_access(
        db: Session,
        user_id: int,
        resource_type: str,
        resource_id: int,
        fields_accessed: list[str],
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log data access for compliance."""
        details = {
            "fields_accessed": fields_accessed,
            "access_type": "read",
        }
        return AuditLogger.log_action(
            db,
            user_id,
            "DATA_ACCESS",
            resource_type,
            resource_id,
            details,
            ip_address,
        )

    @staticmethod
    def log_security_event(
        db: Session,
        user_id: int | None,
        event_name: str,
        severity: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log security events (login attempts, failed auth, etc)."""
        details = details or {}
        details["severity"] = severity
        return AuditLogger.log_action(
            db,
            user_id or 0,
            event_name,
            "SECURITY_EVENT",
            0,
            details,
            ip_address,
            event_type="security",
            resource="security_event",
        )

    @staticmethod
    def _calculate_hash(log_data: dict[str, Any]) -> str:
        """Calculate cryptographic hash of log entry."""
        # Serialize deterministically
        log_string = json.dumps(log_data, sort_keys=True)
        return hashlib.sha256(log_string.encode()).hexdigest()

    @staticmethod
    def verify_chain_integrity(db: Session) -> tuple[bool, list[str]]:
        """
        Verify audit log chain integrity.

        Returns:
            tuple of (is_intact, list_of_broken_hashes)
        """
        logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
        broken = []

        previous_hash = ""
        for log in logs:
            # Verify chain link
            if log.previous_hash != previous_hash:
                broken.append(log.current_hash)

            # Verify log hash
            log_data = {
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "details": json.loads(log.details),
                "ip_address": log.ip_address,
                "previous_hash": log.previous_hash,
            }
            calculated_hash = AuditLogger._calculate_hash(log_data)
            if calculated_hash != log.current_hash:
                broken.append(log.current_hash)

            previous_hash = log.current_hash

        return len(broken) == 0, broken

    @staticmethod
    def get_user_audit_log(
        db: Session,
        user_id: int,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get audit log for a specific user."""
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    @staticmethod
    def get_resource_audit_log(
        db: Session,
        resource_type: str,
        resource_id: int,
    ) -> list[AuditLog]:
        """Get audit log for a specific resource."""
        return db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        ).order_by(
            AuditLog.timestamp.desc()
        ).all()

    @staticmethod
    def get_security_events(
        db: Session,
        severity: str | None = None,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Get security events."""
        query = db.query(AuditLog).filter(
            AuditLog.action.like("SECURITY_%")
        )

        if severity:
            # Parse severity from details
            query = query.filter(AuditLog.details.like(f'%"{severity}"%'))

        return query.order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()


# Create alias for backward compatibility with tests
class AuditLogging:
    """Alias for AuditLogger to match test imports."""

    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        resource: str,
        details: dict[str, Any],
    ) -> AuditLog:
        """Log an action."""
        # Parse resource string to extract type and ID
        resource_parts = resource.split(":")
        resource_type = resource_parts[0] if resource_parts else "unknown"
        resource_id = int(resource_parts[1]) if len(resource_parts) > 1 and resource_parts[1].isdigit() else 0

        # Delegate to AuditLogger to get proper hash chaining
        return AuditLogger.log_action(
            db,
            user_id,
            action,
            resource_type,
            resource_id,
            details,
        )

    @staticmethod
    def log_security_event(
        db: Session,
        user_id: int,
        event: str,
        severity: str,
        details: dict[str, Any],
    ) -> AuditLog:
        """Log a security event."""
        # Delegate to AuditLogger to get proper hash chaining
        return AuditLogger.log_security_event(
            db,
            user_id,
            event,
            severity,
            details,
        )

    @staticmethod
    def log_data_access(
        db: Session,
        user_id: int,
        resource: str,
        action: str,
        resource_type: str,
    ) -> AuditLog:
        """Log data access."""
        # Parse resource string to extract resource_id
        resource_parts = resource.split(":")
        resource_id = int(resource_parts[1]) if len(resource_parts) > 1 and resource_parts[1].isdigit() else 0

        # Delegate to AuditLogger to get proper hash chaining
        return AuditLogger.log_action(
            db,
            user_id,
            action,
            resource_type,
            resource_id,
            {},
            event_type="data_access",
            resource=resource,
        )

    @staticmethod
    def verify_chain_integrity(
        db: Session,
        user_id: int | None = None,
    ) -> tuple[bool, list[str]]:
        """Verify audit log chain integrity."""
        if user_id:
            logs = db.query(AuditLog).filter(
                AuditLog.user_id == user_id
            ).order_by(AuditLog.id.asc()).all()
        else:
            logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()

        broken = []
        previous_hash = ""
        for log in logs:
            # Verify chain link if current_hash exists
            if log.previous_hash != previous_hash and log.current_hash:
                broken.append(str(log.id))

            if log.current_hash:
                previous_hash = log.current_hash

        return len(broken) == 0, broken
