"""Fraud Rule Routes - API endpoints for fraud detection rules"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.fraud_rule_models import (
    FraudRule, RuleSet, RuleType, RuleStatus, RuleAction, RuleCondition
)
from ..services.rule_engine_service import rule_engine_service


router = APIRouter(prefix="/fraud/rules", tags=["Fraud Rules"])


class RuleConditionRequest(BaseModel):
    field: str
    operator: str
    value: Any
    data_type: str = "string"


class CreateRuleRequest(BaseModel):
    rule_code: str
    rule_name: str
    rule_type: RuleType
    description: str
    conditions: List[RuleConditionRequest]
    logic_expression: str
    action: RuleAction
    alert_severity: str = "medium"
    score_weight: float = Field(default=1.0, ge=0, le=100)
    created_by: str


class UpdateRuleRequest(BaseModel):
    rule_name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[List[RuleConditionRequest]] = None
    logic_expression: Optional[str] = None
    action: Optional[RuleAction] = None
    alert_severity: Optional[str] = None
    score_weight: Optional[float] = None


class ToggleRuleRequest(BaseModel):
    is_active: bool


class EvaluateTransactionRequest(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    currency: str = "USD"
    transaction_type: str
    channel: str
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    additional_data: Dict[str, Any] = {}


class CreateRuleSetRequest(BaseModel):
    name: str
    description: str
    rule_ids: List[UUID]
    applicable_channels: List[str]
    created_by: str


@router.post("/", response_model=FraudRule)
async def create_rule(request: CreateRuleRequest):
    """Create a new fraud detection rule"""
    conditions = [
        RuleCondition(
            field=c.field,
            operator=c.operator,
            value=c.value,
            data_type=c.data_type
        )
        for c in request.conditions
    ]
    rule = FraudRule(
        rule_code=request.rule_code,
        rule_name=request.rule_name,
        rule_type=request.rule_type,
        description=request.description,
        conditions=conditions,
        logic_expression=request.logic_expression,
        action=request.action,
        alert_severity=request.alert_severity,
        score_weight=request.score_weight,
        created_by=request.created_by
    )
    return await rule_engine_service.create_rule(rule)


@router.get("/{rule_id}", response_model=FraudRule)
async def get_rule(rule_id: UUID):
    """Get rule by ID"""
    rule = await rule_engine_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=FraudRule)
async def update_rule(rule_id: UUID, request: UpdateRuleRequest):
    """Update a fraud rule"""
    updates = request.model_dump(exclude_none=True)
    if "conditions" in updates:
        updates["conditions"] = [
            RuleCondition(**c) if isinstance(c, dict) else c
            for c in updates["conditions"]
        ]
    rule = await rule_engine_service.update_rule(rule_id, updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/{rule_id}/toggle", response_model=FraudRule)
async def toggle_rule(rule_id: UUID, request: ToggleRuleRequest):
    """Enable or disable a rule"""
    rule = await rule_engine_service.toggle_rule(rule_id, request.is_active)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: UUID):
    """Delete a fraud rule"""
    rule = await rule_engine_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted successfully", "rule_id": str(rule_id)}


@router.get("/", response_model=List[FraudRule])
async def list_rules(
    rule_type: Optional[RuleType] = None,
    status: Optional[RuleStatus] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List fraud rules with optional filters"""
    rules = await rule_engine_service.get_all_rules()
    if rule_type:
        rules = [r for r in rules if r.rule_type == rule_type]
    if status:
        rules = [r for r in rules if r.status == status]
    return rules[offset:offset + limit]


@router.get("/active", response_model=List[FraudRule])
async def get_active_rules():
    """Get all active rules"""
    return await rule_engine_service.get_active_rules()


@router.post("/evaluate")
async def evaluate_transaction(request: EvaluateTransactionRequest):
    """Evaluate a transaction against all active rules"""
    transaction_data = {
        "transaction_id": request.transaction_id,
        "customer_id": request.customer_id,
        "amount": request.amount,
        "currency": request.currency,
        "transaction_type": request.transaction_type,
        "channel": request.channel,
        "device_id": request.device_id,
        "ip_address": request.ip_address,
        **request.additional_data
    }
    results = await rule_engine_service.evaluate_transaction(transaction_data)
    matched_rules = [r for r in results if r.matched]
    total_score = sum(r.score for r in matched_rules)
    highest_action = max(
        [r.action for r in matched_rules],
        default=RuleAction.LOG,
        key=lambda x: ["log", "alert", "challenge", "block"].index(x.value)
    ) if matched_rules else RuleAction.LOG
    return {
        "transaction_id": request.transaction_id,
        "rules_evaluated": len(results),
        "rules_matched": len(matched_rules),
        "total_score": total_score,
        "recommended_action": highest_action.value,
        "rule_results": [r.model_dump() for r in results]
    }


@router.get("/statistics/summary")
async def get_rule_statistics():
    """Get rule statistics"""
    all_rules = await rule_engine_service.get_all_rules()
    active_count = len([r for r in all_rules if r.status == RuleStatus.ACTIVE])
    by_type = {}
    for rule in all_rules:
        type_key = rule.rule_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1
    return {
        "total_rules": len(all_rules),
        "active_rules": active_count,
        "inactive_rules": len(all_rules) - active_count,
        "by_type": by_type
    }
