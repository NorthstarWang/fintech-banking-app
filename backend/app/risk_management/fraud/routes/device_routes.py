"""Device Routes - API endpoints for device fingerprinting and trust management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models.device_models import (
    DeviceFingerprint, DeviceProfile, DeviceSession,
    DeviceTrustLevel, DeviceType, DeviceRiskAssessment
)
from ..services.device_service import device_service


router = APIRouter(prefix="/fraud/devices", tags=["Fraud Devices"])


class RegisterFingerprintRequest(BaseModel):
    device_type: str = "unknown"
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    browser_name: Optional[str] = None
    browser_version: Optional[str] = None
    user_agent: str
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class CreateProfileRequest(BaseModel):
    fingerprint_id: UUID
    customer_id: str


class UpdateTrustLevelRequest(BaseModel):
    trust_level: DeviceTrustLevel
    trust_score: float


class BlockDeviceRequest(BaseModel):
    reason: str


class CreateSessionRequest(BaseModel):
    device_id: UUID
    customer_id: str
    ip_address: str


@router.post("/fingerprints", response_model=DeviceFingerprint)
async def register_fingerprint(request: RegisterFingerprintRequest):
    """Register a new device fingerprint"""
    fingerprint_data = request.model_dump()
    fingerprint = await device_service.register_fingerprint(fingerprint_data)
    return fingerprint


@router.post("/profiles", response_model=DeviceProfile)
async def create_profile(request: CreateProfileRequest):
    """Create a device profile for a customer"""
    profile = await device_service.create_profile(
        request.fingerprint_id,
        request.customer_id
    )
    return profile


@router.get("/profiles/{device_id}", response_model=DeviceProfile)
async def get_profile(device_id: UUID):
    """Get device profile by ID"""
    profile = await device_service.get_profile(device_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Device profile not found")
    return profile


@router.put("/profiles/{device_id}/trust", response_model=DeviceProfile)
async def update_trust_level(device_id: UUID, request: UpdateTrustLevelRequest):
    """Update device trust level"""
    profile = await device_service.update_trust_level(
        device_id,
        request.trust_level,
        request.trust_score
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Device profile not found")
    return profile


@router.post("/profiles/{device_id}/block", response_model=DeviceProfile)
async def block_device(device_id: UUID, request: BlockDeviceRequest):
    """Block a device"""
    profile = await device_service.block_device(device_id, request.reason)
    if not profile:
        raise HTTPException(status_code=404, detail="Device profile not found")
    return profile


@router.post("/profiles/{device_id}/unblock", response_model=DeviceProfile)
async def unblock_device(device_id: UUID):
    """Unblock a device"""
    profile = await device_service.get_profile(device_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Device profile not found")
    profile.is_blocked = False
    profile.block_reason = None
    profile.blocked_at = None
    profile.trust_level = DeviceTrustLevel.VERIFIED
    return profile


@router.get("/profiles/{device_id}/risk", response_model=DeviceRiskAssessment)
async def assess_device_risk(device_id: UUID):
    """Assess risk for a device"""
    return await device_service.assess_device_risk(device_id)


@router.post("/sessions", response_model=DeviceSession)
async def create_session(request: CreateSessionRequest):
    """Create a new device session"""
    session = await device_service.create_session(
        request.device_id,
        request.customer_id,
        request.ip_address
    )
    return session


@router.get("/customer/{customer_id}/devices")
async def get_customer_devices(customer_id: str):
    """Get all devices associated with a customer"""
    # This would typically query the repository
    return {"customer_id": customer_id, "devices": []}


@router.get("/blocked")
async def get_blocked_devices(limit: int = Query(default=100, le=500)):
    """Get all blocked devices"""
    return {"blocked_devices": []}


@router.get("/suspicious")
async def get_suspicious_devices(limit: int = Query(default=100, le=500)):
    """Get all suspicious devices"""
    return {"suspicious_devices": []}


@router.get("/statistics/summary")
async def get_device_statistics():
    """Get device statistics"""
    return await device_service.get_statistics()


@router.post("/analyze")
async def analyze_device(request: RegisterFingerprintRequest):
    """Analyze a device fingerprint for fraud indicators"""
    fingerprint_data = request.model_dump()
    fingerprint = await device_service.register_fingerprint(fingerprint_data)
    # Create temporary profile for risk assessment
    profile = await device_service.create_profile(
        fingerprint.fingerprint_id,
        "analysis_temp"
    )
    risk = await device_service.assess_device_risk(profile.device_id)
    return {
        "fingerprint": fingerprint,
        "risk_assessment": risk
    }
