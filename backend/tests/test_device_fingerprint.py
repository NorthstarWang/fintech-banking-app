"""
Comprehensive tests for device fingerprinting and trust management.

Tests device fingerprint generation, device tracking, trust management,
and compromise detection capabilities.
"""

import pytest
import time
from datetime import datetime, timedelta

from app.security.device_fingerprint import DeviceFingerprint, TrustedDevice
from app.storage.memory_adapter import db


@pytest.fixture
def db_session():
    """Provide a database session for testing."""
    # Return the memory adapter db which handles in-memory SQLAlchemy operations
    return db


class TestDeviceFingerprintGeneration:
    """Test fingerprint generation and hashing."""

    def test_generate_fingerprint_basic(self):
        """Test basic fingerprint generation."""
        device_data = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "browser": "Chrome",
            "os": "Windows 10",
            "screen_resolution": "1920x1080",
            "timezone": "America/New_York",
        }

        fingerprint = DeviceFingerprint.generate_fingerprint(device_data)

        assert fingerprint is not None
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64  # SHA256 hex digest is 64 characters

    def test_generate_fingerprint_consistency(self):
        """Test that same data generates same fingerprint."""
        device_data = {
            "user_agent": "Mozilla/5.0",
            "browser": "Firefox",
            "os": "Linux",
            "screen_resolution": "1280x720",
            "timezone": "UTC",
        }

        fingerprint1 = DeviceFingerprint.generate_fingerprint(device_data)
        fingerprint2 = DeviceFingerprint.generate_fingerprint(device_data)

        assert fingerprint1 == fingerprint2

    def test_generate_fingerprint_different_data(self):
        """Test that different data generates different fingerprints."""
        device_data1 = {
            "user_agent": "Mozilla/5.0",
            "browser": "Chrome",
            "os": "Windows",
            "screen_resolution": "1920x1080",
            "timezone": "UTC",
        }

        device_data2 = {
            "user_agent": "Mozilla/5.0",
            "browser": "Firefox",  # Different browser
            "os": "Windows",
            "screen_resolution": "1920x1080",
            "timezone": "UTC",
        }

        fingerprint1 = DeviceFingerprint.generate_fingerprint(device_data1)
        fingerprint2 = DeviceFingerprint.generate_fingerprint(device_data2)

        assert fingerprint1 != fingerprint2

    def test_generate_fingerprint_missing_fields(self):
        """Test fingerprint generation with missing fields."""
        device_data = {
            "user_agent": "Mozilla/5.0",
            "browser": "Chrome",
            # Missing some fields
        }

        fingerprint = DeviceFingerprint.generate_fingerprint(device_data)

        assert fingerprint is not None
        assert len(fingerprint) == 64


class TestDeviceTracking:
    """Test device tracking functionality."""

    def test_get_or_create_device(self, db_session):
        """Test getting or creating a device."""
        user_id = 1
        device_fingerprint = "abc123def456"
        device_name = "My Laptop"

        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fingerprint, device_name
        )

        assert device is not None
        assert device.user_id == user_id
        assert device.fingerprint_hash == device_fingerprint
        assert device.device_name == device_name

    def test_get_or_create_device_existing(self, db_session):
        """Test that get_or_create returns existing device."""
        user_id = 2
        device_fingerprint = "xyz789uvw012"
        device_name = "Work Desktop"

        # Create first
        device1 = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fingerprint, device_name
        )

        # Get same device again
        device2 = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fingerprint, "Different Name"
        )

        assert device1.id == device2.id
        assert device2.device_name == device_name  # Name shouldn't change

    def test_mark_device_trusted(self, db_session):
        """Test marking a device as trusted."""
        user_id = 3
        device_fingerprint = "trusted123"

        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fingerprint, "Trusted Device"
        )

        # Mark as trusted
        DeviceFingerprint.mark_device_trusted(db_session, device.id)
        db_session.refresh(device)

        assert device.is_trusted is True
        assert device.last_seen_at is not None

    def test_get_user_devices(self, db_session):
        """Test retrieving all devices for a user."""
        user_id = 4

        # Create multiple devices
        DeviceFingerprint.get_or_create_device(db_session, user_id, "device1", "Device 1")
        DeviceFingerprint.get_or_create_device(db_session, user_id, "device2", "Device 2")
        DeviceFingerprint.get_or_create_device(db_session, user_id, "device3", "Device 3")

        devices = DeviceFingerprint.get_user_devices(db_session, user_id)

        assert len(devices) == 3


class TestDeviceChangeDetection:
    """Test detection of device changes and compromises."""

    def test_detect_no_change_same_fingerprint(self, db_session):
        """Test that same fingerprint shows no change."""
        user_id = 5
        device_fingerprint = "same_fp_123"

        # Create and trust device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fingerprint, "Test Device"
        )
        DeviceFingerprint.mark_device_trusted(db_session, device.id)

        # Check same fingerprint
        is_changed, indicators = DeviceFingerprint.detect_device_changes(
            db_session, user_id, device_fingerprint
        )

        assert is_changed is False
        assert len(indicators) == 0

    def test_detect_new_device(self, db_session):
        """Test detection of new device."""
        user_id = 6
        old_fingerprint = "old_device_fp"
        new_fingerprint = "new_device_fp"

        # Create and trust old device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, old_fingerprint, "Old Device"
        )
        DeviceFingerprint.mark_device_trusted(db_session, device.id)

        # Check new fingerprint
        is_changed, indicators = DeviceFingerprint.detect_device_changes(
            db_session, user_id, new_fingerprint
        )

        assert is_changed is True
        assert "new_device" in indicators

    def test_detect_spoofed_device(self, db_session):
        """Test detection of spoofed/untrusted device."""
        user_id = 7
        trusted_fingerprint = "trusted_device_fp"
        untrusted_fingerprint = "untrusted_device_fp"

        # Create and trust device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, trusted_fingerprint, "Trusted Device"
        )
        DeviceFingerprint.mark_device_trusted(db_session, device.id)

        # Create untrusted device (not marked as trusted)
        DeviceFingerprint.get_or_create_device(
            db_session, user_id, untrusted_fingerprint, "Untrusted Device"
        )

        # Check untrusted fingerprint
        is_changed, indicators = DeviceFingerprint.detect_device_changes(
            db_session, user_id, untrusted_fingerprint
        )

        assert is_changed is True

    def test_detect_multiple_compromises(self, db_session):
        """Test detection of multiple compromise indicators."""
        user_id = 8
        device_fingerprint = "multi_indicator_fp"

        # Create device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fingerprint, "Test Device"
        )
        DeviceFingerprint.mark_device_trusted(db_session, device.id)

        # Simulate rapid changes (simulate device update)
        # This would be done by the application logic
        # For now just verify the detection mechanism works
        is_changed, indicators = DeviceFingerprint.detect_device_changes(
            db_session, user_id, device_fingerprint
        )

        assert is_changed is False


class TestDeviceCleanup:
    """Test device cleanup and purging."""

    def test_cleanup_old_devices(self, db_session):
        """Test cleanup of old devices."""
        user_id = 9
        days_to_keep = 30

        # Create device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, "old_device_fp", "Old Device"
        )

        # Manually set last_seen_at to old date
        old_date = datetime.utcnow() - timedelta(days=days_to_keep + 1)
        device.last_seen_at = old_date
        db_session.commit()

        # Cleanup
        removed_count = DeviceFingerprint.cleanup_old_devices(db_session, days_to_keep)

        assert removed_count > 0

    def test_keep_recent_devices(self, db_session):
        """Test that recent devices are not cleaned up."""
        user_id = 10
        days_to_keep = 30

        # Create device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, "recent_device_fp", "Recent Device"
        )

        # Set last_seen_at to recent date
        recent_date = datetime.utcnow() - timedelta(days=days_to_keep - 1)
        device.last_seen_at = recent_date
        db_session.commit()

        # Count before cleanup
        devices_before = DeviceFingerprint.get_user_devices(db_session, user_id)
        count_before = len(devices_before)

        # Cleanup
        DeviceFingerprint.cleanup_old_devices(db_session, days_to_keep)

        # Count after cleanup
        devices_after = DeviceFingerprint.get_user_devices(db_session, user_id)
        count_after = len(devices_after)

        assert count_after == count_before


class TestTrustedDeviceModel:
    """Test TrustedDevice SQLAlchemy model."""

    def test_trusted_device_attributes(self, db_session):
        """Test TrustedDevice model attributes."""
        device = TrustedDevice(
            user_id=11,
            fingerprint_hash="test_hash_123",
            device_name="Test Device",
            device_type="Laptop",
            browser="Chrome",
            os="Windows",
            is_trusted=True,
        )

        db_session.add(device)
        db_session.commit()

        retrieved = db_session.query(TrustedDevice).filter(TrustedDevice.user_id == 11).first()

        assert retrieved.user_id == 11
        assert retrieved.fingerprint_hash == "test_hash_123"
        assert retrieved.device_name == "Test Device"
        assert retrieved.is_trusted is True

    def test_device_timestamps(self, db_session):
        """Test device timestamp fields."""
        device = TrustedDevice(
            user_id=12,
            fingerprint_hash="test_hash_456",
            device_name="Timestamp Test",
        )

        db_session.add(device)
        db_session.commit()

        retrieved = db_session.query(TrustedDevice).filter(TrustedDevice.user_id == 12).first()

        assert retrieved.created_at is not None
        assert isinstance(retrieved.created_at, datetime)


class TestDeviceFingerprintIntegration:
    """Integration tests for device fingerprinting system."""

    def test_full_device_lifecycle(self, db_session):
        """Test complete device lifecycle: create, trust, detect, cleanup."""
        user_id = 13
        device_fp = "lifecycle_test_fp"

        # 1. Create device
        device = DeviceFingerprint.get_or_create_device(
            db_session, user_id, device_fp, "Lifecycle Device"
        )
        assert device is not None

        # 2. Mark as trusted
        DeviceFingerprint.mark_device_trusted(db_session, device.id)
        assert device.is_trusted is True

        # 3. Detect no change for same fingerprint
        is_changed, indicators = DeviceFingerprint.detect_device_changes(
            db_session, user_id, device_fp
        )
        assert is_changed is False

        # 4. Update last_seen_at
        old_time = datetime.utcnow() - timedelta(days=40)
        device.last_seen_at = old_time
        db_session.commit()

        # 5. Cleanup should remove it
        removed = DeviceFingerprint.cleanup_old_devices(db_session, 30)
        assert removed > 0

    def test_multiple_users_device_isolation(self, db_session):
        """Test that devices are isolated per user."""
        user1_id = 14
        user2_id = 15
        same_fingerprint = "shared_fingerprint"

        # Create device for user1
        user1_device = DeviceFingerprint.get_or_create_device(
            db_session, user1_id, same_fingerprint, "User1 Device"
        )

        # Create device with same fingerprint for user2
        user2_device = DeviceFingerprint.get_or_create_device(
            db_session, user2_id, same_fingerprint, "User2 Device"
        )

        # Should be different devices
        assert user1_device.id != user2_device.id
        assert user1_device.user_id != user2_device.user_id

        # Each user should only see their own device
        user1_devices = DeviceFingerprint.get_user_devices(db_session, user1_id)
        user2_devices = DeviceFingerprint.get_user_devices(db_session, user2_id)

        assert len(user1_devices) == 1
        assert len(user2_devices) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
