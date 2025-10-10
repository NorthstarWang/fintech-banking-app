"""
Device fingerprinting and trust management system.

Captures device signatures and manages trusted devices per user.
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session, declarative_base

# Create SQLAlchemy base for security models
Base = declarative_base()


class TrustedDevice(Base):
    """Model for storing trusted devices."""

    __tablename__ = "trusted_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    device_fingerprint = Column(String(256), unique=True, index=True)
    device_name = Column(String(255))
    device_info = Column(Text)  # JSON string
    browser_fingerprint = Column(String(256))
    screen_resolution = Column(String(50))
    timezone = Column(String(100))
    is_trusted = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45), index=True)  # IPv4 or IPv6


class DeviceFingerprint:
    """Device fingerprinting service."""

    @staticmethod
    def generate_fingerprint(
        user_agent: str,
        ip_address: str,
        browser_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a device fingerprint from browser and system data.

        Args:
            user_agent: User agent string
            ip_address: Client IP address
            browser_data: Additional browser fingerprint data

        Returns:
            Hash of combined fingerprint data
        """
        fingerprint_data = {
            "user_agent": user_agent,
            "ip_address": ip_address,
            "browser_info": browser_data or {},
        }

        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    @staticmethod
    def get_or_create_device(
        db: Session,
        user_id: int,
        fingerprint: str,
        device_info: dict[str, Any],
        ip_address: str,
    ) -> TrustedDevice:
        """Get or create a device record."""
        device = db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id,
            TrustedDevice.device_fingerprint == fingerprint,
        ).first()

        if not device:
            device = TrustedDevice(
                user_id=user_id,
                device_fingerprint=fingerprint,
                device_name=device_info.get("name", "Unknown Device"),
                device_info=json.dumps(device_info),
                browser_fingerprint=device_info.get("browser_fingerprint", ""),
                screen_resolution=device_info.get("screen_resolution", ""),
                timezone=device_info.get("timezone", ""),
                ip_address=ip_address,
            )
            db.add(device)
            db.commit()

        # Update last seen
        device.last_seen = datetime.utcnow()
        db.commit()

        return device

    @staticmethod
    def is_trusted_device(device: TrustedDevice) -> bool:
        """Check if device is trusted."""
        return device.is_trusted

    @staticmethod
    def mark_device_trusted(db: Session, device_id: int) -> None:
        """Mark a device as trusted."""
        device = db.query(TrustedDevice).filter(TrustedDevice.id == device_id).first()
        if device:
            device.is_trusted = True
            db.commit()

    @staticmethod
    def detect_device_changes(
        current_device: TrustedDevice,
        new_device_info: dict[str, Any],
    ) -> list[str]:
        """
        Detect changes in device characteristics that might indicate compromise.

        Returns:
            List of detected changes
        """
        changes = []
        current_info = json.loads(current_device.device_info)

        # Check screen resolution change
        if (current_info.get("screen_resolution") !=
                new_device_info.get("screen_resolution")):
            changes.append("screen_resolution")

        # Check timezone change
        if current_info.get("timezone") != new_device_info.get("timezone"):
            changes.append("timezone")

        # Check browser fingerprint change
        if (current_info.get("browser_fingerprint") !=
                new_device_info.get("browser_fingerprint")):
            changes.append("browser_fingerprint")

        # Check OS change
        if current_info.get("os") != new_device_info.get("os"):
            changes.append("os")

        return changes

    @staticmethod
    def get_user_devices(db: Session, user_id: int) -> list[TrustedDevice]:
        """Get all devices for a user."""
        return db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id
        ).order_by(TrustedDevice.last_seen.desc()).all()

    @staticmethod
    def remove_device(db: Session, device_id: int, user_id: int) -> bool:
        """Remove a device from trusted devices."""
        device = db.query(TrustedDevice).filter(
            TrustedDevice.id == device_id,
            TrustedDevice.user_id == user_id,
        ).first()

        if device:
            db.delete(device)
            db.commit()
            return True

        return False

    @staticmethod
    def cleanup_old_devices(db: Session, days: int = 90) -> int:
        """Remove devices not seen in specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        devices = db.query(TrustedDevice).filter(
            TrustedDevice.last_seen < cutoff_date
        ).delete()
        db.commit()
        return devices
