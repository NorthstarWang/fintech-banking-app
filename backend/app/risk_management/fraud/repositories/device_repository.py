"""Device Repository - Data access layer for device fingerprints and profiles"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from ..models.device_models import DeviceFingerprint, DeviceProfile, DeviceSession, DeviceTrustLevel


class DeviceRepository:
    def __init__(self):
        self._fingerprints: dict[UUID, DeviceFingerprint] = {}
        self._profiles: dict[UUID, DeviceProfile] = {}
        self._sessions: dict[UUID, DeviceSession] = {}
        self._hash_index: dict[str, UUID] = {}
        self._customer_device_index: dict[str, list[UUID]] = {}

    async def save_fingerprint(self, fingerprint: DeviceFingerprint) -> DeviceFingerprint:
        self._fingerprints[fingerprint.fingerprint_id] = fingerprint
        self._hash_index[fingerprint.device_hash] = fingerprint.fingerprint_id
        return fingerprint

    async def find_fingerprint_by_id(self, fingerprint_id: UUID) -> DeviceFingerprint | None:
        return self._fingerprints.get(fingerprint_id)

    async def find_fingerprint_by_hash(self, device_hash: str) -> DeviceFingerprint | None:
        fingerprint_id = self._hash_index.get(device_hash)
        if fingerprint_id:
            return self._fingerprints.get(fingerprint_id)
        return None

    async def save_profile(self, profile: DeviceProfile) -> DeviceProfile:
        self._profiles[profile.device_id] = profile
        if profile.primary_customer_id:
            if profile.primary_customer_id not in self._customer_device_index:
                self._customer_device_index[profile.primary_customer_id] = []
            if profile.device_id not in self._customer_device_index[profile.primary_customer_id]:
                self._customer_device_index[profile.primary_customer_id].append(profile.device_id)
        return profile

    async def find_profile_by_id(self, device_id: UUID) -> DeviceProfile | None:
        return self._profiles.get(device_id)

    async def find_profiles_by_customer(self, customer_id: str) -> list[DeviceProfile]:
        device_ids = self._customer_device_index.get(customer_id, [])
        return [self._profiles[did] for did in device_ids if did in self._profiles]

    async def find_profiles_by_trust_level(self, trust_level: DeviceTrustLevel) -> list[DeviceProfile]:
        return [p for p in self._profiles.values() if p.trust_level == trust_level]

    async def find_blocked_profiles(self) -> list[DeviceProfile]:
        return [p for p in self._profiles.values() if p.is_blocked]

    async def find_suspicious_profiles(self) -> list[DeviceProfile]:
        return [p for p in self._profiles.values() if p.trust_level == DeviceTrustLevel.SUSPICIOUS]

    async def find_profiles_by_ip(self, ip_address: str) -> list[DeviceProfile]:
        return [p for p in self._profiles.values() if ip_address in p.ip_addresses]

    async def update_profile(self, profile: DeviceProfile) -> DeviceProfile:
        profile.updated_at = datetime.now(UTC)
        self._profiles[profile.device_id] = profile
        return profile

    async def save_session(self, session: DeviceSession) -> DeviceSession:
        self._sessions[session.session_id] = session
        return session

    async def find_session_by_id(self, session_id: UUID) -> DeviceSession | None:
        return self._sessions.get(session_id)

    async def find_sessions_by_device(self, device_id: UUID, limit: int = 100) -> list[DeviceSession]:
        sessions = [s for s in self._sessions.values() if s.device_id == device_id]
        return sorted(sessions, key=lambda x: x.started_at, reverse=True)[:limit]

    async def find_sessions_by_customer(self, customer_id: str, limit: int = 100) -> list[DeviceSession]:
        sessions = [s for s in self._sessions.values() if s.customer_id == customer_id]
        return sorted(sessions, key=lambda x: x.started_at, reverse=True)[:limit]

    async def find_active_sessions(self) -> list[DeviceSession]:
        return [s for s in self._sessions.values() if s.is_active]

    async def find_recent_sessions(self, hours: int = 24) -> list[DeviceSession]:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return [s for s in self._sessions.values() if s.started_at >= cutoff]

    async def update_session(self, session: DeviceSession) -> DeviceSession:
        self._sessions[session.session_id] = session
        return session

    async def end_session(self, session_id: UUID) -> DeviceSession | None:
        session = self._sessions.get(session_id)
        if session:
            session.ended_at = datetime.now(UTC)
            session.is_active = False
        return session

    async def get_device_statistics(self) -> dict[str, Any]:
        total_devices = len(self._profiles)
        by_trust_level = {}
        for profile in self._profiles.values():
            level_key = profile.trust_level.value
            by_trust_level[level_key] = by_trust_level.get(level_key, 0) + 1
        blocked_count = len([p for p in self._profiles.values() if p.is_blocked])
        return {
            "total_devices": total_devices,
            "by_trust_level": by_trust_level,
            "blocked_devices": blocked_count,
            "active_sessions": len([s for s in self._sessions.values() if s.is_active])
        }

    async def count_profiles(self) -> int:
        return len(self._profiles)

    async def count_fingerprints(self) -> int:
        return len(self._fingerprints)


device_repository = DeviceRepository()
