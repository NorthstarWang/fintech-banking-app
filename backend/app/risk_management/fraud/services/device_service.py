"""Device Service - Device fingerprinting and trust management"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import hashlib
from ..models.device_models import (
    DeviceFingerprint, DeviceProfile, DeviceSession,
    DeviceTrustLevel, DeviceType, DeviceRiskAssessment, DeviceStatistics
)


class DeviceService:
    def __init__(self):
        self._fingerprints: Dict[UUID, DeviceFingerprint] = {}
        self._profiles: Dict[UUID, DeviceProfile] = {}
        self._sessions: Dict[UUID, DeviceSession] = {}

    def _calculate_device_hash(self, fingerprint_data: Dict[str, Any]) -> str:
        data_str = f"{fingerprint_data.get('user_agent', '')}{fingerprint_data.get('screen_resolution', '')}{fingerprint_data.get('timezone', '')}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:32]

    async def register_fingerprint(self, fingerprint_data: Dict[str, Any]) -> DeviceFingerprint:
        device_hash = self._calculate_device_hash(fingerprint_data)
        fingerprint = DeviceFingerprint(
            device_hash=device_hash,
            device_type=DeviceType(fingerprint_data.get("device_type", "unknown")),
            os_name=fingerprint_data.get("os_name"),
            os_version=fingerprint_data.get("os_version"),
            browser_name=fingerprint_data.get("browser_name"),
            browser_version=fingerprint_data.get("browser_version"),
            user_agent=fingerprint_data.get("user_agent", ""),
            screen_resolution=fingerprint_data.get("screen_resolution"),
            timezone=fingerprint_data.get("timezone"),
            language=fingerprint_data.get("language")
        )
        self._fingerprints[fingerprint.fingerprint_id] = fingerprint
        return fingerprint

    async def create_profile(self, fingerprint_id: UUID, customer_id: str) -> DeviceProfile:
        profile = DeviceProfile(
            fingerprint_id=fingerprint_id,
            associated_customers=[customer_id],
            primary_customer_id=customer_id
        )
        self._profiles[profile.device_id] = profile
        return profile

    async def get_profile(self, device_id: UUID) -> Optional[DeviceProfile]:
        return self._profiles.get(device_id)

    async def update_trust_level(self, device_id: UUID, trust_level: DeviceTrustLevel, trust_score: float) -> Optional[DeviceProfile]:
        profile = self._profiles.get(device_id)
        if profile:
            profile.trust_level = trust_level
            profile.trust_score = trust_score
            profile.updated_at = datetime.utcnow()
        return profile

    async def block_device(self, device_id: UUID, reason: str) -> Optional[DeviceProfile]:
        profile = self._profiles.get(device_id)
        if profile:
            profile.is_blocked = True
            profile.block_reason = reason
            profile.blocked_at = datetime.utcnow()
            profile.trust_level = DeviceTrustLevel.BLOCKED
        return profile

    async def create_session(self, device_id: UUID, customer_id: str, ip_address: str) -> DeviceSession:
        session = DeviceSession(
            device_id=device_id,
            customer_id=customer_id,
            ip_address=ip_address
        )
        self._sessions[session.session_id] = session
        profile = self._profiles.get(device_id)
        if profile:
            profile.total_sessions += 1
            if ip_address not in profile.ip_addresses:
                profile.ip_addresses.append(ip_address)
        return session

    async def assess_device_risk(self, device_id: UUID) -> DeviceRiskAssessment:
        profile = self._profiles.get(device_id)
        risk_score = 50.0
        risk_factors = []
        if profile:
            if profile.fraud_incidents > 0:
                risk_score += 30.0
                risk_factors.append({"factor": "previous_fraud", "score": 30.0})
            if profile.trust_level == DeviceTrustLevel.NEW:
                risk_score += 20.0
                risk_factors.append({"factor": "new_device", "score": 20.0})
            if len(profile.associated_customers) > 3:
                risk_score += 15.0
                risk_factors.append({"factor": "multiple_customers", "score": 15.0})
        return DeviceRiskAssessment(
            device_id=device_id,
            risk_score=min(risk_score, 100.0),
            risk_level="high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low",
            risk_factors=risk_factors
        )

    async def get_statistics(self) -> DeviceStatistics:
        stats = DeviceStatistics(total_devices=len(self._profiles))
        for profile in self._profiles.values():
            stats.by_trust_level[profile.trust_level.value] = stats.by_trust_level.get(profile.trust_level.value, 0) + 1
            if profile.is_blocked:
                stats.blocked_devices += 1
            if profile.trust_level == DeviceTrustLevel.SUSPICIOUS:
                stats.suspicious_devices += 1
        return stats


device_service = DeviceService()
