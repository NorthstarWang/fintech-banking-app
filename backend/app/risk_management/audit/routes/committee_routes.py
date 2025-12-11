"""Committee API Routes"""

from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.committee_models import CommitteeType
from ..services.committee_service import committee_service

router = APIRouter(prefix="/committees", tags=["Board Committees"])


class CommitteeCreateRequest(BaseModel):
    committee_name: str
    committee_type: CommitteeType
    charter: str
    mandate: List[str]
    responsibilities: List[str]
    minimum_members: int
    meeting_frequency: str


class MemberAppointmentRequest(BaseModel):
    committee_id: UUID
    member_id: UUID
    member_name: str
    role: str
    term_end_date: date
    is_independent: bool
    expertise_relevant: List[str]


class MeetingScheduleRequest(BaseModel):
    committee_id: UUID
    meeting_date: date
    meeting_time: str
    meeting_type: str
    location: str
    agenda: List[Dict[str, Any]]


class ResolutionRequest(BaseModel):
    committee_id: UUID
    meeting_id: UUID
    subject: str
    resolution_text: str
    proposed_by: str
    seconded_by: str
    votes_for: int
    votes_against: int
    votes_abstained: int
    implementation_required: bool = False
    implementation_deadline: Optional[date] = None
    implementation_owner: str = ""


@router.post("/", response_model=dict)
async def establish_committee(request: CommitteeCreateRequest):
    committee = await committee_service.establish_committee(
        committee_name=request.committee_name, committee_type=request.committee_type,
        charter=request.charter, mandate=request.mandate,
        responsibilities=request.responsibilities, minimum_members=request.minimum_members,
        meeting_frequency=request.meeting_frequency
    )
    return {"committee_id": str(committee.committee_id), "committee_name": committee.committee_name}


@router.get("/", response_model=List[dict])
async def list_committees(active_only: bool = True):
    if active_only:
        committees = await committee_service.repository.find_active_committees()
    else:
        committees = await committee_service.repository.find_all_committees()
    return [{"committee_id": str(c.committee_id), "committee_name": c.committee_name, "committee_type": c.committee_type.value} for c in committees]


@router.post("/members", response_model=dict)
async def appoint_member(request: MemberAppointmentRequest):
    member = await committee_service.appoint_member(
        committee_id=request.committee_id, member_id=request.member_id,
        member_name=request.member_name, role=request.role,
        term_end_date=request.term_end_date, is_independent=request.is_independent,
        expertise_relevant=request.expertise_relevant
    )
    return {"membership_id": str(member.membership_id), "role": member.role}


@router.get("/{committee_id}/members", response_model=List[dict])
async def get_committee_members(committee_id: UUID):
    members = await committee_service.repository.find_members_by_committee(committee_id)
    return [{"membership_id": str(m.membership_id), "member_name": m.member_name, "role": m.role} for m in members]


@router.post("/meetings", response_model=dict)
async def schedule_meeting(request: MeetingScheduleRequest):
    meeting = await committee_service.schedule_meeting(
        committee_id=request.committee_id, meeting_date=request.meeting_date,
        meeting_time=request.meeting_time, meeting_type=request.meeting_type,
        location=request.location, agenda=request.agenda
    )
    return {"meeting_id": str(meeting.meeting_id), "meeting_reference": meeting.meeting_reference}


@router.get("/{committee_id}/meetings", response_model=List[dict])
async def get_committee_meetings(committee_id: UUID):
    meetings = await committee_service.repository.find_meetings_by_committee(committee_id)
    return [{"meeting_id": str(m.meeting_id), "meeting_reference": m.meeting_reference, "meeting_date": str(m.meeting_date)} for m in meetings]


@router.post("/meetings/{meeting_id}/record", response_model=dict)
async def record_meeting(
    meeting_id: UUID,
    attendees: List[str] = Query(...),
    discussions: List[Dict[str, Any]] = Query(default=[]),
    decisions: List[Dict[str, Any]] = Query(default=[]),
    action_items: List[Dict[str, Any]] = Query(default=[])
):
    meeting = await committee_service.record_meeting(meeting_id, attendees, discussions, decisions, action_items)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting_id": str(meeting.meeting_id), "minutes_status": meeting.minutes_status}


@router.post("/meetings/{meeting_id}/approve-minutes", response_model=dict)
async def approve_minutes(meeting_id: UUID):
    meeting = await committee_service.approve_minutes(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting_id": str(meeting.meeting_id), "minutes_status": meeting.minutes_status}


@router.post("/resolutions", response_model=dict)
async def pass_resolution(request: ResolutionRequest):
    resolution = await committee_service.pass_resolution(
        committee_id=request.committee_id, meeting_id=request.meeting_id,
        subject=request.subject, resolution_text=request.resolution_text,
        proposed_by=request.proposed_by, seconded_by=request.seconded_by,
        votes_for=request.votes_for, votes_against=request.votes_against,
        votes_abstained=request.votes_abstained,
        implementation_required=request.implementation_required,
        implementation_deadline=request.implementation_deadline,
        implementation_owner=request.implementation_owner
    )
    return {"resolution_id": str(resolution.resolution_id), "resolution_reference": resolution.resolution_reference, "passed": resolution.passed}


@router.get("/{committee_id}/resolutions", response_model=List[dict])
async def get_committee_resolutions(committee_id: UUID):
    resolutions = await committee_service.repository.find_resolutions_by_committee(committee_id)
    return [{"resolution_id": str(r.resolution_id), "resolution_reference": r.resolution_reference, "subject": r.subject, "passed": r.passed} for r in resolutions]


@router.get("/statistics", response_model=dict)
async def get_committee_statistics():
    return await committee_service.get_statistics()
