"""
Device Fingerprinting Models

Defines data structures for device identification and trust scoring.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class DeviceTrustLevel(str, Enum):
    TRUSTED = "trusted"
    KNOWN = "known"
    NEW = "new"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


class DeviceFingerprint(BaseModel):
    fingerprint_id: UUID = Field(default_factory=uuid4)
    device_hash: str

    device_type: DeviceType
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    browser_name: Optional[str] = None
    browser_version: Optional[str] = None

    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

    user_agent: str
    plugins_hash: Optional[str] = None
    fonts_hash: Optional[str] = None
    canvas_hash: Optional[str] = None
    webgl_hash: Optional[str] = None

    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceProfile(BaseModel):
    device_id: UUID = Field(default_factory=uuid4)
    fingerprint_id: UUID

    trust_level: DeviceTrustLevel = DeviceTrustLevel.NEW
    trust_score: float = Field(ge=0, le=100, default=50)

    associated_customers: List[str] = Field(default_factory=list)
    primary_customer_id: Optional[str] = None

    ip_addresses: List[str] = Field(default_factory=list)
    locations: List[Dict[str, Any]] = Field(default_factory=list)

    total_sessions: int = 0
    total_transactions: int = 0
    successful_transactions: int = 0
    failed_transactions: int = 0
    fraud_incidents: int = 0

    is_blocked: bool = False
    block_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    risk_flags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceSession(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    device_id: UUID
    customer_id: str

    ip_address: str
    location: Optional[Dict[str, Any]] = None

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)

    is_active: bool = True
    session_type: str = "web"

    activities: List[Dict[str, Any]] = Field(default_factory=list)
    risk_events: List[str] = Field(default_factory=list)


class DeviceRiskAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    device_id: UUID

    risk_score: float = Field(ge=0, le=100)
    risk_level: str

    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    assessed_at: datetime = Field(default_factory=datetime.utcnow)


class DeviceStatistics(BaseModel):
    total_devices: int = 0
    by_trust_level: Dict[str, int] = Field(default_factory=dict)
    by_device_type: Dict[str, int] = Field(default_factory=dict)
    blocked_devices: int = 0
    new_devices_today: int = 0
    suspicious_devices: int = 0
