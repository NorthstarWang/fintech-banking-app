"""Audit & Governance Routes"""

from .internal_audit_routes import router as internal_audit_router
from .external_audit_routes import router as external_audit_router
from .governance_routes import router as governance_router
from .committee_routes import router as committee_router
from .policy_routes import router as policy_router
from .compliance_testing_routes import router as compliance_testing_router
from .issue_management_routes import router as issue_management_router
from .audit_planning_routes import router as audit_planning_router

__all__ = [
    "internal_audit_router",
    "external_audit_router",
    "governance_router",
    "committee_router",
    "policy_router",
    "compliance_testing_router",
    "issue_management_router",
    "audit_planning_router",
]
