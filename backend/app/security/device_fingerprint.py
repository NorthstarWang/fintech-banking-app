"""
Device fingerprinting and trust management system.

Captures device signatures and manages trusted devices per user.
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

# Import models from memory models instead of defining SQLAlchemy models
from app.models.memory_models import TrustedDevice


class DeviceFingerprint:
    """Device fingerprinting service."""

    @staticmethod
    def generate_fingerprint(device_data: dict[str, Any]) -> str:
        """
        Generate a device fingerprint from browser and system data.

        Args:
            device_data: Dictionary containing device characteristics like
                        user_agent, browser, os, screen_resolution, timezone, etc.

        Returns:
            Hash of combined fingerprint data (SHA256 hex digest - 64 chars)
        """
        # Sort keys to ensure consistent hashing
        fingerprint_string = json.dumps(device_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    @staticmethod
    def get_or_create_device(
        db: Session,
        user_id: int,
        fingerprint_hash: str,
        device_name: str,
    ) -> TrustedDevice:
        """
        Get or create a device record.

        Args:
            db: Database session
            user_id: User ID
            fingerprint_hash: Device fingerprint hash
            device_name: Human-readable device name

        Returns:
            TrustedDevice object
        """
        device = db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id,
            TrustedDevice.fingerprint_hash == fingerprint_hash,
        ).first()

        if not device:
            device = TrustedDevice(
                user_id=user_id,
                fingerprint_hash=fingerprint_hash,
                device_name=device_name,
                first_seen=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                is_trusted=False,
            )
            db.add(device)
            db.commit()

        # Update last seen
        device.last_seen_at = datetime.utcnow()
        db.commit()

        # Ensure the device object is properly tracked for future updates
        # by setting its session reference and making it point to the actual store dict
        if hasattr(device, '_data') and hasattr(db, '_get_session'):
            session = db._get_session()
            device._session = session

            # Make device._data point to the actual dict in the store
            # so that updates to the store are reflected in this object
            store = session._get_store_for_model(TrustedDevice)
            for item in store:
                if item.get('id') == device.id:
                    device._data = item
                    device._original_data = item.copy()
                    break

        return device

    @staticmethod
    def is_trusted_device(device: TrustedDevice) -> bool:
        """Check if device is trusted."""
        return device.is_trusted

    @staticmethod
    def mark_device_trusted(db: Session, device_id: int) -> None:
        """Mark a device as trusted."""
        # Update the device directly in the data store to ensure
        # all references to this device see the update
        if hasattr(db, '_get_session'):
            session = db._get_session()
            store = session._get_store_for_model(TrustedDevice)
            for item in store:
                if item.get('id') == device_id:
                    # Update the dict in place, not replace it
                    item['is_trusted'] = True
                    item['last_seen_at'] = datetime.utcnow()
                    break

    @staticmethod
    def detect_device_changes(
        db: Session,
        user_id: int,
        fingerprint_hash: str,
    ) -> tuple[bool, list[str]]:
        """
        Detect changes in device characteristics that might indicate compromise.

        Args:
            db: Database session
            user_id: User ID
            fingerprint_hash: Current device fingerprint hash

        Returns:
            Tuple of (is_changed, indicators) where is_changed is True if device
            is new or untrusted, and indicators is list of change indicators
        """
        indicators = []

        # Get user's trusted devices
        trusted_devices = db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id,
            TrustedDevice.is_trusted == True,
        ).all()

        # Check if this fingerprint matches any trusted device
        matching_device = None
        for device in trusted_devices:
            if device.fingerprint_hash == fingerprint_hash:
                matching_device = device
                break

        if not matching_device:
            # Check if device exists but is not trusted
            untrusted_device = db.query(TrustedDevice).filter(
                TrustedDevice.user_id == user_id,
                TrustedDevice.fingerprint_hash == fingerprint_hash,
                TrustedDevice.is_trusted == False,
            ).first()

            if untrusted_device:
                indicators.append("untrusted_device")
                return True, indicators
            else:
                indicators.append("new_device")
                return True, indicators

        # Device matches a trusted device - no change
        return False, indicators

    @staticmethod
    def get_user_devices(db: Session, user_id: int) -> list[TrustedDevice]:
        """Get all devices for a user."""
        return db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id
        ).order_by(TrustedDevice.last_seen_at.desc()).all()

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

        # Get all devices and filter manually to ensure we catch all old ones
        all_devices = db.query(TrustedDevice).all()
        devices_to_delete = []

        for device in all_devices:
            if device.last_seen_at and device.last_seen_at < cutoff_date:
                devices_to_delete.append(device)

        count = len(devices_to_delete)
        for device in devices_to_delete:
            db.delete(device)

        if count > 0:
            db.commit()

        return count
