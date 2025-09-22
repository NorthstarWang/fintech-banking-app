from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional, Any
from datetime import datetime

from ..storage.memory_adapter import db
from ..models import Note, User
from ..utils.auth import get_current_user
from ..utils.session_manager import session_manager
from pydantic import BaseModel

# Request/Response models
class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = []
    is_encrypted: bool = False
    related_account_id: Optional[int] = None
    related_transaction_id: Optional[int] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_encrypted: Optional[bool] = None

class NoteResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    tags: List[str]
    is_encrypted: bool
    related_account_id: Optional[int]
    related_transaction_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

router = APIRouter()

@router.get("/", response_model=List[NoteResponse])
async def get_notes(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all notes for the current user with optional filtering"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Base query for user's notes
    query = db_session.query(Note).filter(Note.user_id == current_user.id)
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Note.title.ilike(search_pattern)) | 
            (Note.content.ilike(search_pattern))
        )
    
    # Apply tag filter if provided
    if tag:
        query = query.filter(Note.tags.contains([tag]))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and get results
    notes = query.offset(skip).limit(limit).all()
    
        session_id=session_id,
        user_id=current_user.id,
        table_name="notes",
        record_count=len(notes),
        human_readable=f"Retrieved {len(notes)} notes for user {current_user.username}"
    )
    
    return notes

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get a specific note by ID"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    note = db_session.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
        session_id=session_id,
        user_id=current_user.id,
        table_name="notes",
        record_count=1,
        human_readable=f"Retrieved note '{note.title}' for user {current_user.username}"
    )
    
    return note

@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new note"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Create new note
    new_note = Note(
        user_id=current_user.id,
        title=note_data.title,
        content=note_data.content,
        tags=note_data.tags,
        is_encrypted=note_data.is_encrypted
    )
    
    db_session.add(new_note)
    db_session.commit()
    db_session.refresh(new_note)
    
        session_id=session_id,
        user_id=current_user.id,
        operation="CREATE",
        table_name="notes",
        record_id=new_note.id,
        human_readable=f"Created note '{new_note.title}' for user {current_user.username}",
        details={
            "note_id": new_note.id,
            "title": new_note.title,
            "tags": new_note.tags,
            "is_encrypted": new_note.is_encrypted
        }
    )
    
    # Add related fields for response
    new_note.related_account_id = note_data.related_account_id
    new_note.related_transaction_id = note_data.related_transaction_id
    
    return new_note

@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update an existing note"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Get existing note
    note = db_session.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Update fields if provided
    update_data = note_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    
    note.updated_at = datetime.utcnow()
    
    db_session.commit()
    db_session.refresh(note)
    
        session_id=session_id,
        user_id=current_user.id,
        operation="UPDATE",
        table_name="notes",
        record_id=note.id,
        human_readable=f"Updated note '{note.title}' for user {current_user.username}",
        details={
            "note_id": note.id,
            "updated_fields": list(update_data.keys())
        }
    )
    
    return note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Delete a note"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Get existing note
    note = db_session.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Store note info for logging
    note_title = note.title
    
    # Delete the note
    db_session.delete(note)
    db_session.commit()
    
        session_id=session_id,
        user_id=current_user.id,
        operation="DELETE",
        table_name="notes",
        record_id=note_id,
        human_readable=f"Deleted note '{note_title}' for user {current_user.username}",
        details={
            "note_id": note_id,
            "title": note_title
        }
    )
    
    return None

@router.get("/tags/all", response_model=List[str])
async def get_all_tags(
    request: Request,
    current_user: User = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all unique tags used by the current user"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Get all notes for the user
    notes = db_session.query(Note).filter(Note.user_id == current_user.id).all()
    
    # Extract unique tags
    all_tags = set()
    for note in notes:
        if note.tags:
            all_tags.update(note.tags)
    
        session_id=session_id,
        user_id=current_user.id,
        table_name="notes",
        record_count=len(notes),
        human_readable=f"Retrieved {len(all_tags)} unique tags for user {current_user.username}"
    )
    
    return sorted(list(all_tags))