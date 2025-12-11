"""Governance API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..services.governance_service import governance_service

router = APIRouter(prefix="/governance", tags=["Corporate Governance"])


class FrameworkCreateRequest(BaseModel):
    framework_name: str
    framework_version: str
    description: str
    principles: List[str]
    governance_structure: Dict[str, Any]
    roles_responsibilities: Dict[str, List[str]]
    approved_by: str


class BoardMemberRequest(BaseModel):
    member_name: str
    position: str
    member_type: str
    term_end_date: date
    qualifications: List[str]
    expertise_areas: List[str]
    annual_fee: Decimal


class BoardMeetingRequest(BaseModel):
    meeting_type: str
    meeting_date: date
    meeting_time: str
    location: str
    agenda_items: List[Dict[str, Any]]


class ConflictDeclarationRequest(BaseModel):
    declarant_name: str
    declarant_position: str
    conflict_type: str
    description: str
    related_party: str
    nature_of_interest: str
    review_committee: str


@router.post("/frameworks", response_model=dict)
async def create_framework(request: FrameworkCreateRequest):
    framework = await governance_service.create_framework(
        framework_name=request.framework_name, framework_version=request.framework_version,
        description=request.description, principles=request.principles,
        governance_structure=request.governance_structure,
        roles_responsibilities=request.roles_responsibilities,
        approved_by=request.approved_by
    )
    return {"framework_id": str(framework.framework_id), "framework_name": framework.framework_name}


@router.get("/frameworks", response_model=List[dict])
async def list_frameworks():
    frameworks = await governance_service.repository.find_all_frameworks()
    return [{"framework_id": str(f.framework_id), "framework_name": f.framework_name, "status": f.status} for f in frameworks]


@router.post("/board-members", response_model=dict)
async def appoint_board_member(request: BoardMemberRequest):
    member = await governance_service.appoint_board_member(
        member_name=request.member_name, position=request.position,
        member_type=request.member_type, term_end_date=request.term_end_date,
        qualifications=request.qualifications, expertise_areas=request.expertise_areas,
        annual_fee=request.annual_fee
    )
    return {"member_id": str(member.member_id), "member_name": member.member_name}


@router.get("/board-members", response_model=List[dict])
async def list_board_members(active_only: bool = True, independent_only: bool = False):
    if independent_only:
        members = await governance_service.repository.find_independent_members()
    elif active_only:
        members = await governance_service.repository.find_active_board_members()
    else:
        members = await governance_service.repository.find_all_board_members()
    return [{"member_id": str(m.member_id), "member_name": m.member_name, "position": m.position, "member_type": m.member_type} for m in members]


@router.post("/board-meetings", response_model=dict)
async def schedule_board_meeting(request: BoardMeetingRequest):
    meeting = await governance_service.schedule_board_meeting(
        meeting_type=request.meeting_type, meeting_date=request.meeting_date,
        meeting_time=request.meeting_time, location=request.location,
        agenda_items=request.agenda_items
    )
    return {"meeting_id": str(meeting.meeting_id), "meeting_date": str(meeting.meeting_date)}


@router.get("/board-meetings", response_model=List[dict])
async def list_board_meetings():
    meetings = await governance_service.repository.find_all_board_meetings()
    return [{"meeting_id": str(m.meeting_id), "meeting_type": m.meeting_type, "meeting_date": str(m.meeting_date), "status": m.status} for m in meetings]


@router.post("/board-meetings/{meeting_id}/attendance", response_model=dict)
async def record_attendance(meeting_id: UUID, attendees: List[str] = Query(...), absentees: List[str] = Query(default=[])):
    meeting = await governance_service.record_meeting_attendance(meeting_id, attendees, absentees)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting_id": str(meeting.meeting_id), "quorum_present": meeting.quorum_present}


@router.post("/conflicts", response_model=dict)
async def declare_conflict(request: ConflictDeclarationRequest):
    conflict = await governance_service.declare_conflict(
        declarant_name=request.declarant_name, declarant_position=request.declarant_position,
        conflict_type=request.conflict_type, description=request.description,
        related_party=request.related_party, nature_of_interest=request.nature_of_interest,
        review_committee=request.review_committee
    )
    return {"conflict_id": str(conflict.conflict_id), "status": conflict.status}


@router.get("/conflicts", response_model=List[dict])
async def list_conflicts(pending_only: bool = False):
    if pending_only:
        conflicts = await governance_service.repository.find_pending_conflicts()
    else:
        conflicts = await governance_service.repository.find_all_conflicts()
    return [{"conflict_id": str(c.conflict_id), "declarant_name": c.declarant_name, "status": c.status} for c in conflicts]


@router.post("/conflicts/{conflict_id}/review", response_model=dict)
async def review_conflict(conflict_id: UUID, decision: str = Query(...), mitigation_measures: List[str] = Query(default=[])):
    conflict = await governance_service.review_conflict(conflict_id, decision, mitigation_measures)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return {"conflict_id": str(conflict.conflict_id), "decision": conflict.decision}


@router.get("/statistics", response_model=dict)
async def get_governance_statistics():
    return await governance_service.get_statistics()
