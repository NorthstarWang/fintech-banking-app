"""Audit & Governance Routes"""

from .audit_planning_routes import router as audit_planning_router
from .committee_routes import router as committee_router
from .compliance_testing_routes import router as compliance_testing_router
from .external_audit_routes import router as external_audit_router
from .governance_routes import router as governance_router
from .internal_audit_routes import router as internal_audit_router
from .issue_management_routes import router as issue_management_router
from .policy_routes import router as policy_router

__all__ = [
    "audit_planning_router",
    "committee_router",
    "compliance_testing_router",
    "external_audit_router",
    "governance_router",
    "internal_audit_router",
    "issue_management_router",
    "policy_router",
]
