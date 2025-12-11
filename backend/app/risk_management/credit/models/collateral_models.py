"""Collateral Models - Collateral and security management models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class CollateralType(str, Enum):
    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    EQUIPMENT = "equipment"
    INVENTORY = "inventory"
    RECEIVABLES = "receivables"
    SECURITIES = "securities"
    CASH = "cash"
    GUARANTEE = "guarantee"
    OTHER = "other"


class CollateralStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    PERFECTED = "perfected"
    RELEASED = "released"
    IMPAIRED = "impaired"
    LIQUIDATED = "liquidated"


class ValuationType(str, Enum):
    MARKET = "market"
    APPRAISED = "appraised"
    BOOK = "book"
    FORCED_SALE = "forced_sale"
    DISCOUNTED = "discounted"


class Collateral(BaseModel):
    collateral_id: UUID = Field(default_factory=uuid4)
    collateral_code: str
    collateral_type: CollateralType
    description: str
    owner_id: str
    owner_name: str
    status: CollateralStatus = CollateralStatus.PENDING
    original_value: float
    current_value: float
    haircut_percentage: float = Field(default=0.0, ge=0, le=100)
    adjusted_value: float
    currency: str = "USD"
    location: Optional[str] = None
    registration_number: Optional[str] = None
    registration_date: Optional[date] = None
    perfection_status: str = "pending"
    perfection_date: Optional[date] = None
    insurance_policy: Optional[str] = None
    insurance_expiry: Optional[date] = None
    linked_facilities: List[UUID] = []
    total_allocation: float = 0.0
    available_value: float = 0.0
    last_valuation_date: Optional[date] = None
    next_valuation_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CollateralValuation(BaseModel):
    valuation_id: UUID = Field(default_factory=uuid4)
    collateral_id: UUID
    valuation_type: ValuationType
    valuation_date: date
    valuer_name: str
    valuer_company: Optional[str] = None
    market_value: float
    forced_sale_value: float
    insurance_value: Optional[float] = None
    land_value: Optional[float] = None
    building_value: Optional[float] = None
    valuation_methodology: str
    assumptions: List[str] = []
    value_drivers: List[str] = []
    risk_factors: List[str] = []
    valuation_report_url: Optional[str] = None
    expiry_date: date
    status: str = "current"
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollateralAllocation(BaseModel):
    allocation_id: UUID = Field(default_factory=uuid4)
    collateral_id: UUID
    facility_id: UUID
    loan_id: Optional[UUID] = None
    allocation_amount: float
    allocation_percentage: float
    priority_ranking: int = 1
    effective_date: date
    expiry_date: Optional[date] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollateralHaircut(BaseModel):
    haircut_id: UUID = Field(default_factory=uuid4)
    collateral_type: CollateralType
    sub_type: Optional[str] = None
    standard_haircut: float
    stressed_haircut: float
    currency_haircut: float = 0.0
    volatility_adjustment: float = 0.0
    liquidity_adjustment: float = 0.0
    total_haircut: float
    effective_date: date
    review_date: date
    approved_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollateralMonitoring(BaseModel):
    monitoring_id: UUID = Field(default_factory=uuid4)
    collateral_id: UUID
    monitoring_date: date
    value_change_percentage: float
    ltv_ratio: float
    margin_call_triggered: bool = False
    margin_call_amount: Optional[float] = None
    insurance_status: str
    physical_inspection_due: bool = False
    legal_review_due: bool = False
    issues_identified: List[str] = []
    recommendations: List[str] = []
    monitored_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Guarantee(BaseModel):
    guarantee_id: UUID = Field(default_factory=uuid4)
    guarantee_type: str  # corporate, personal, bank, government
    guarantor_id: str
    guarantor_name: str
    guarantor_rating: Optional[str] = None
    guaranteed_facility_id: UUID
    guarantee_amount: float
    guarantee_percentage: float
    currency: str = "USD"
    effective_date: date
    expiry_date: date
    guarantee_document: Optional[str] = None
    status: str = "active"
    legal_enforceability: str = "enforceable"
    recovery_rate_assumption: float = Field(default=0.5, ge=0, le=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollateralStatistics(BaseModel):
    total_collateral_count: int = 0
    total_original_value: float = 0.0
    total_current_value: float = 0.0
    total_adjusted_value: float = 0.0
    by_type: Dict[str, float] = {}
    by_status: Dict[str, int] = {}
    average_haircut: float = 0.0
    average_ltv: float = 0.0
