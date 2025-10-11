from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..models import (
    BlockUserRequest,
    BulkMessageUpdate,
    DirectMessageCreate,
    DirectMessageReply,
    DirectMessageResponse,
    MessageFolderCreate,
    MessageFolderResponse,
    MessageMoveRequest,
    MessageSettingsResponse,
    MessageSettingsUpdate,
    NotificationType,
)
from ..models.memory_models import (
    BlockedUser,
    DirectMessage,
    MessageAttachment,
    MessageFolder,
    MessageSettings,
    Notification,
    User,
)
from ..storage.memory_adapter import and_, db, desc, joinedload, or_
from ..utils.auth import get_current_user

router = APIRouter()

def is_user_blocked(db_session: Any, sender_id: int, recipient_id: int) -> bool:
    """Check if sender is blocked by recipient"""
    blocked = db_session.query(BlockedUser).filter(
        BlockedUser.user_id == recipient_id,
        BlockedUser.blocked_user_id == sender_id
    ).first()
    return blocked is not None

def create_message_notification(db_session: Any, recipient_id: int, sender_username: str, subject: str):
    """Create notification for new message"""
    notification = Notification(
        user_id=recipient_id,
        type=NotificationType.NEW_MESSAGE,
        title=f"New message from {sender_username}",
        message=subject,
        action_url="/messages"
    )
    db_session.add(notification)

@router.post("", response_model=DirectMessageResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: Request,
    message_data: DirectMessageCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Send a direct message to another user"""

    # Get recipient user
    recipient = db_session.query(User).filter(
        User.username == message_data.recipient_username
    ).first()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )

    # Check if sender is blocked
    if is_user_blocked(db_session, current_user['user_id'], recipient.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot send messages to this user"
        )

    # Create message
    message = DirectMessage(
        sender_id=current_user['user_id'],
        recipient_id=recipient.id,
        subject=message_data.subject,
        message=message_data.message,
        priority=message_data.priority,
        is_draft=message_data.is_draft,
        is_read=False,
        sent_at=datetime.utcnow()
    )

    db_session.add(message)
    db_session.flush()

    # Add attachments if any
    if message_data.attachments:
        for attachment_data in message_data.attachments:
            attachment = MessageAttachment(
                message_id=message.id,
                filename=attachment_data['filename'],
                file_type=attachment_data['file_type'],
                file_size=attachment_data['file_size']
            )
            db_session.add(attachment)

    db_session.commit()
    db_session.refresh(message)

    # Create notification if not a draft
    if not message_data.is_draft:
        create_message_notification(
            db_session,
            recipient.id,
            current_user['username'],
            message_data.subject
        )
        db_session.commit()

    # Prepare response
    response = DirectMessageResponse.from_orm(message)
    response.sender_username = current_user['username']
    response.recipient_username = recipient.username

    # Load attachments properly
    if message.attachments:
        response.attachments = list(message.attachments)
    elif message_data.attachments:
        response.attachments = message_data.attachments

    return response

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/inbox", response_model=list[DirectMessageResponse])
async def get_inbox(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get inbox messages"""
    messages = db_session.query(DirectMessage).options(
        joinedload(DirectMessage.sender),
        joinedload(DirectMessage.attachments)
    ).filter(
        DirectMessage.recipient_id == current_user['user_id'],
        DirectMessage.deleted_by_recipient == False,
        DirectMessage.is_draft == False
    ).order_by(desc(DirectMessage.sent_at)).offset(offset).limit(limit).all()

    results = []
    for msg in messages:
        # Load sender manually
        sender = db_session.query(User).filter(User.id == msg.sender_id).first()

        response = DirectMessageResponse.from_orm(msg)
        response.sender_username = sender.username if sender else None
        response.recipient_username = current_user['username']

        # Load attachments manually
        attachments = db_session.query(MessageAttachment).filter(
            MessageAttachment.message_id == msg.id
        ).all()
        if attachments:
            response.attachments = list(attachments)
        results.append(response)

    return results

@router.get("/sent", response_model=list[DirectMessageResponse])
async def get_sent_messages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get sent messages"""
    messages = db_session.query(DirectMessage).options(
        joinedload(DirectMessage.recipient),
        joinedload(DirectMessage.attachments)
    ).filter(
        DirectMessage.sender_id == current_user['user_id'],
        DirectMessage.deleted_by_sender == False,
        DirectMessage.is_draft == False
    ).order_by(desc(DirectMessage.sent_at)).offset(offset).limit(limit).all()

    results = []
    for msg in messages:
        # Load recipient manually
        recipient = db_session.query(User).filter(User.id == msg.recipient_id).first()

        response = DirectMessageResponse.from_orm(msg)
        response.sender_username = current_user['username']
        response.recipient_username = recipient.username if recipient else None

        # Load attachments manually
        attachments = db_session.query(MessageAttachment).filter(
            MessageAttachment.message_id == msg.id
        ).all()
        if attachments:
            response.attachments = list(attachments)
        results.append(response)

    return results

@router.get("/search", response_model=list[DirectMessageResponse])
async def search_messages(
    query: str,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Search messages"""
    search_pattern = f"%{query}%"

    messages = db_session.query(DirectMessage).options(
        joinedload(DirectMessage.sender),
        joinedload(DirectMessage.recipient)
    ).filter(
        or_(
            and_(
                DirectMessage.sender_id == current_user['user_id'],
                DirectMessage.deleted_by_sender == False
            ),
            and_(
                DirectMessage.recipient_id == current_user['user_id'],
                DirectMessage.deleted_by_recipient == False
            )
        ),
        or_(
            DirectMessage.subject.ilike(search_pattern),
            DirectMessage.message.ilike(search_pattern)
        ),
        DirectMessage.is_draft == False
    ).order_by(desc(DirectMessage.sent_at)).all()

    results = []
    for msg in messages:
        # Load sender and recipient manually
        sender = db_session.query(User).filter(User.id == msg.sender_id).first()
        recipient = db_session.query(User).filter(User.id == msg.recipient_id).first()

        response = DirectMessageResponse.from_orm(msg)
        response.sender_username = sender.username if sender else None
        response.recipient_username = recipient.username if recipient else None
        results.append(response)

    return results

@router.post("/drafts", response_model=DirectMessageResponse)
async def save_draft(
    request: Request,
    draft_data: DirectMessageCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Save a message draft"""
    draft_data.is_draft = True
    return await send_message(request, draft_data, current_user, db_session)

@router.get("/drafts", response_model=list[DirectMessageResponse])
async def get_drafts(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all drafts"""
    drafts = db_session.query(DirectMessage).options(
        joinedload(DirectMessage.recipient)
    ).filter(
        DirectMessage.sender_id == current_user['user_id'],
        DirectMessage.is_draft == True,
        DirectMessage.deleted_by_sender == False
    ).order_by(desc(DirectMessage.created_at)).all()

    results = []
    for draft in drafts:
        # Load recipient manually
        recipient = db_session.query(User).filter(User.id == draft.recipient_id).first() if draft.recipient_id else None

        response = DirectMessageResponse.from_orm(draft)
        response.sender_username = current_user['username']
        response.recipient_username = recipient.username if recipient else None
        results.append(response)

    return results

@router.post("/{message_id}/mark-read")
async def mark_message_read(
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Mark a single message as read"""
    message = db_session.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        DirectMessage.recipient_id == current_user['user_id'],
        DirectMessage.is_read == False
    ).first()

    if not message:
        # Either message doesn't exist, user is not the recipient, or already read
        return {"message": "No action needed"}

    message.is_read = True
    message.read_at = datetime.utcnow()
    db_session.commit()

    return {"message": "Message marked as read"}

@router.put("/bulk/read")
async def bulk_mark_read(
    bulk_data: BulkMessageUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Bulk mark messages as read"""
    updated = db_session.query(DirectMessage).filter(
        DirectMessage.id.in_(bulk_data.message_ids),
        DirectMessage.recipient_id == current_user['user_id'],
        DirectMessage.is_read == False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    }, synchronize_session=False)

    db_session.commit()

    return {"updated_count": updated}

@router.post("/folders", response_model=MessageFolderResponse)
async def create_folder(
    folder_data: MessageFolderCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a message folder"""
    # Check if folder already exists
    existing = db_session.query(MessageFolder).filter(
        MessageFolder.user_id == current_user['user_id'],
        MessageFolder.folder_name == folder_data.folder_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder with this name already exists"
        )

    folder = MessageFolder(
        user_id=current_user['user_id'],
        folder_name=folder_data.folder_name,
        color=folder_data.color
    )

    db_session.add(folder)
    db_session.commit()
    db_session.refresh(folder)

    return MessageFolderResponse.from_orm(folder)

@router.get("/settings", response_model=MessageSettingsResponse)
async def get_message_settings(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get message notification settings"""
    settings = db_session.query(MessageSettings).filter(
        MessageSettings.user_id == current_user['user_id']
    ).first()

    if not settings:
        # Create default settings
        settings = MessageSettings(
            user_id=current_user['user_id'],
            email_on_new_message=True,
            push_notifications=True,
            notification_sound=True,
            auto_mark_read=False
        )
        db_session.add(settings)
        db_session.commit()
        db_session.refresh(settings)

    return MessageSettingsResponse.from_orm(settings)

@router.put("/settings", response_model=MessageSettingsResponse)
async def update_message_settings(
    settings_data: MessageSettingsUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update message notification settings"""
    settings = db_session.query(MessageSettings).filter(
        MessageSettings.user_id == current_user['user_id']
    ).first()

    if not settings:
        settings = MessageSettings(user_id=current_user['user_id'])
        db_session.add(settings)

    # Update only provided fields
    update_data = settings_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    db_session.commit()
    db_session.refresh(settings)

    return MessageSettingsResponse.from_orm(settings)

@router.post("/block")
async def block_user(
    block_data: BlockUserRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Block a user from sending messages"""
    # Get user to block
    user_to_block = db_session.query(User).filter(
        User.username == block_data.username
    ).first()

    if not user_to_block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already blocked
    existing = db_session.query(BlockedUser).filter(
        BlockedUser.user_id == current_user['user_id'],
        BlockedUser.blocked_user_id == user_to_block.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already blocked"
        )

    blocked = BlockedUser(
        user_id=current_user['user_id'],
        blocked_user_id=user_to_block.id,
        reason=block_data.reason
    )

    db_session.add(blocked)
    db_session.commit()

    return {"message": "User blocked successfully"}

@router.get("/blocked", response_model=list[str])
async def get_blocked_users(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get list of blocked users"""
    # Memory adapter doesn't support multi-model queries, so we need to do this manually
    blocked_users = db_session.query(BlockedUser).filter(
        BlockedUser.user_id == current_user['user_id']
    ).all()

    result = []
    for blocked in blocked_users:
        user = db_session.query(User).filter(User.id == blocked.blocked_user_id).first()
        if user:
            result.append(user.username)

    return result

@router.get("/thread/{message_id}", response_model=list[DirectMessageResponse])
async def get_message_thread(
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get message thread (original message and all replies)"""
    # Get the root message
    message = db_session.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        or_(
            DirectMessage.sender_id == current_user['user_id'],
            DirectMessage.recipient_id == current_user['user_id']
        )
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Find root message
    root_id = message_id
    if message.parent_message_id:
        root_id = message.parent_message_id

    # Get all messages in thread
    thread_messages = db_session.query(DirectMessage).options(
        joinedload(DirectMessage.sender),
        joinedload(DirectMessage.recipient)
    ).filter(
        or_(
            DirectMessage.id == root_id,
            DirectMessage.parent_message_id == root_id
        ),
        or_(
            DirectMessage.sender_id == current_user['user_id'],
            DirectMessage.recipient_id == current_user['user_id']
        )
    ).order_by(DirectMessage.sent_at).all()

    results = []
    for msg in thread_messages:
        # Load sender and recipient manually
        sender = db_session.query(User).filter(User.id == msg.sender_id).first()
        recipient = db_session.query(User).filter(User.id == msg.recipient_id).first()

        response = DirectMessageResponse.from_orm(msg)
        response.sender_username = sender.username if sender else None
        response.recipient_username = recipient.username if recipient else None
        results.append(response)

    return results

# PARAMETERIZED ROUTES LAST

@router.get("/{message_id}", response_model=DirectMessageResponse)
async def get_message(
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get a specific message"""
    message = db_session.query(DirectMessage).options(
        joinedload(DirectMessage.sender),
        joinedload(DirectMessage.recipient),
        joinedload(DirectMessage.attachments)
    ).filter(
        DirectMessage.id == message_id,
        or_(
            and_(DirectMessage.sender_id == current_user['user_id'],
                 DirectMessage.deleted_by_sender == False),
            and_(DirectMessage.recipient_id == current_user['user_id'],
                 DirectMessage.deleted_by_recipient == False)
        )
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Load sender and recipient manually since memory adapter doesn't support relationship loading
    sender = db_session.query(User).filter(User.id == message.sender_id).first()
    recipient = db_session.query(User).filter(User.id == message.recipient_id).first()

    response = DirectMessageResponse.from_orm(message)
    response.sender_username = sender.username if sender else None
    response.recipient_username = recipient.username if recipient else None

    # Load attachments manually
    attachments = db_session.query(MessageAttachment).filter(
        MessageAttachment.message_id == message.id
    ).all()

    if attachments:
        response.attachments = list(attachments)

    return response

@router.put("/{message_id}/read", response_model=DirectMessageResponse)
async def mark_message_read(
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Mark a message as read"""
    message = db_session.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        DirectMessage.recipient_id == current_user['user_id'],
        DirectMessage.deleted_by_recipient == False
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    message.is_read = True
    message.read_at = datetime.utcnow()

    db_session.commit()
    db_session.refresh(message)

    # Load relationships for response
    sender = db_session.query(User).filter(User.id == message.sender_id).first()
    recipient = db_session.query(User).filter(User.id == message.recipient_id).first()

    response = DirectMessageResponse.from_orm(message)
    response.sender_username = sender.username if sender else None
    response.recipient_username = recipient.username if recipient else None

    return response

@router.post("/{message_id}/reply", response_model=DirectMessageResponse)
async def reply_to_message(
    request: Request,
    message_id: int,
    reply_data: DirectMessageReply,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Reply to a message"""
    # Get original message
    original = db_session.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        or_(
            DirectMessage.sender_id == current_user['user_id'],
            DirectMessage.recipient_id == current_user['user_id']
        )
    ).first()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original message not found"
        )

    # Determine recipient (reply to sender if we're the recipient, or to recipient if we're the sender)
    if original.recipient_id == current_user['user_id']:
        recipient_id = original.sender_id
        recipient = db_session.query(User).filter(User.id == recipient_id).first()
    else:
        recipient_id = original.recipient_id
        recipient = db_session.query(User).filter(User.id == recipient_id).first()

    # Check if blocked
    if is_user_blocked(db_session, current_user['user_id'], recipient_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot send messages to this user"
        )

    # Create reply
    reply = DirectMessage(
        sender_id=current_user['user_id'],
        recipient_id=recipient_id,
        subject=f"Re: {original.subject}",
        message=reply_data.message,
        priority=original.priority,
        parent_message_id=message_id,
        is_draft=False,
        is_read=False,
        sent_at=datetime.utcnow()
    )

    db_session.add(reply)
    db_session.commit()
    db_session.refresh(reply)

    # Create notification
    create_message_notification(
        db_session,
        recipient_id,
        current_user['username'],
        reply.subject
    )
    db_session.commit()

    response = DirectMessageResponse.from_orm(reply)
    response.sender_username = current_user['username']
    response.recipient_username = recipient.username if recipient else None

    return response

@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Delete a message (mark as deleted for user)"""
    message = db_session.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        or_(
            DirectMessage.sender_id == current_user['user_id'],
            DirectMessage.recipient_id == current_user['user_id']
        )
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Mark as deleted for the appropriate user
    if message.sender_id == current_user['user_id']:
        message.deleted_by_sender = True
    if message.recipient_id == current_user['user_id']:
        message.deleted_by_recipient = True

    db_session.commit()

    return {"message": "Message deleted successfully"}

@router.put("/{message_id}/move")
async def move_message_to_folder(
    message_id: int,
    move_data: MessageMoveRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Move message to folder"""
    # Verify folder belongs to user
    folder = db_session.query(MessageFolder).filter(
        MessageFolder.id == move_data.folder_id,
        MessageFolder.user_id == current_user['user_id']
    ).first()

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    # Update message
    message = db_session.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        or_(
            DirectMessage.sender_id == current_user['user_id'],
            DirectMessage.recipient_id == current_user['user_id']
        )
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    message.folder_id = move_data.folder_id
    db_session.commit()

    return {"message": "Message moved successfully"}
