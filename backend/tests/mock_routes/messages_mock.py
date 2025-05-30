"""
Mock implementation for messages routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.repositories.data_manager import data_manager

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    return next((u for u in data_manager.users if u["username"] == username), None)

@router.get("")
async def get_messages(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all messages for current user."""
    messages = []
    for m in data_manager.messages:
        if m["recipient_id"] == current_user["id"] or m["sender_id"] == current_user["id"]:
            # Add usernames to response
            sender = next((u for u in data_manager.users if u["id"] == m["sender_id"]), None)
            recipient = next((u for u in data_manager.users if u["id"] == m["recipient_id"]), None)
            message = m.copy()
            message["sender_username"] = sender["username"] if sender else "unknown"
            message["recipient_username"] = recipient["username"] if recipient else "unknown"
            messages.append(message)
    return messages


@router.post("", status_code=200)  # Changed from 201 to 200
async def send_message(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Send a message."""
    # Get recipient by username
    recipient_username = data.get("recipient_username")
    recipient = get_user_by_username(recipient_username)
    
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    message = {
        "id": str(len(data_manager.messages) + 1),
        "sender_id": current_user["id"],
        "sender_username": current_user["username"],
        "recipient_id": recipient["id"],
        "recipient_username": recipient["username"],
        "subject": data.get("subject", ""),
        "message": data.get("message", ""),  # Changed from "body" to "message"
        "body": data.get("message", ""),  # Keep body for compatibility
        "priority": data.get("priority", "normal"),
        "is_read": False,  # Changed from "read" to "is_read"
        "read": False,  # Keep for compatibility
        "sent_at": datetime.utcnow().isoformat(),  # Changed from "created_at" to "sent_at"
        "created_at": datetime.utcnow().isoformat(),  # Keep for compatibility
        "attachments": data.get("attachments", [])  # Support attachments on send
    }
    
    data_manager.messages.append(message)
    return message


@router.get("/inbox")
async def get_inbox(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get inbox messages."""
    messages = []
    for m in data_manager.messages:
        if m["recipient_id"] == current_user["id"]:
            sender = next((u for u in data_manager.users if u["id"] == m["sender_id"]), None)
            message = m.copy()
            message["sender_username"] = sender["username"] if sender else "unknown"
            messages.append(message)
    return messages


@router.get("/sent")
async def get_sent(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get sent messages."""
    messages = []
    for m in data_manager.messages:
        if m["sender_id"] == current_user["id"]:
            recipient = next((u for u in data_manager.users if u["id"] == m["recipient_id"]), None)
            message = m.copy()
            message["recipient_username"] = recipient["username"] if recipient else "unknown"
            messages.append(message)
    return messages


@router.get("/search")
async def search_messages(query: str = Query(..., alias="query"), current_user: Dict[str, Any] = Depends(get_current_user)):
    """Search messages."""
    results = []
    for m in data_manager.messages:
        if m["recipient_id"] == current_user["id"] or m["sender_id"] == current_user["id"]:
            search_text = query.lower()
            if (search_text in m.get("subject", "").lower() or 
                search_text in m.get("message", "").lower() or
                search_text in m.get("body", "").lower()):
                # Add usernames
                sender = next((u for u in data_manager.users if u["id"] == m["sender_id"]), None)
                recipient = next((u for u in data_manager.users if u["id"] == m["recipient_id"]), None)
                message = m.copy()
                message["sender_username"] = sender["username"] if sender else "unknown"
                message["recipient_username"] = recipient["username"] if recipient else "unknown"
                results.append(message)
    return results


@router.get("/drafts")
async def get_drafts(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get draft messages."""
    drafts = [m for m in data_manager.messages 
              if m.get("sender_id") == current_user["id"] and m.get("is_draft", False)]
    return drafts


@router.post("/drafts", status_code=200)
async def save_draft(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Save a draft message."""
    draft = {
        "id": str(len(data_manager.messages) + 1),
        "sender_id": current_user["id"],
        "sender_username": current_user["username"],
        "subject": data.get("subject", ""),
        "message": data.get("message", ""),
        "is_draft": True,
        "created_at": datetime.utcnow().isoformat()
    }
    data_manager.messages.append(draft)
    return draft


@router.get("/folders")
async def get_folders(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get message folders."""
    return [
        {"id": "1", "name": "Inbox", "count": 0},
        {"id": "2", "name": "Sent", "count": 0},
        {"id": "3", "name": "Drafts", "count": 0},
        {"id": "4", "name": "Trash", "count": 0}
    ]


@router.post("/folders", status_code=200)
async def create_folder(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new folder."""
    return {
        "id": "5",
        "name": data.get("name", "New Folder"),
        "count": 0
    }


@router.get("/notifications")
async def get_unread_notifications(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get unread message count."""
    unread_count = sum(1 for m in data_manager.messages 
                      if m["recipient_id"] == current_user["id"] and not m.get("is_read", False))
    return {"unread_count": unread_count}


@router.post("/bulk", status_code=200)
async def bulk_operations(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Perform bulk operations on messages."""
    operation = data.get("operation", "")
    message_ids = data.get("message_ids", [])
    
    count = 0
    for msg_id in message_ids:
        message = next((m for m in data_manager.messages if m["id"] == msg_id), None)
        if message and (message["recipient_id"] == current_user["id"] or message["sender_id"] == current_user["id"]):
            if operation == "mark_read":
                message["is_read"] = True
                message["read"] = True
                count += 1
            elif operation == "delete":
                data_manager.messages.remove(message)
                count += 1
    
    return {
        "operation": operation,
        "affected_count": count,
        "message": f"Bulk operation completed on {count} messages"
    }


@router.post("/block", status_code=200)
async def block_sender(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Block a sender."""
    username = data.get("username")
    user_to_block = get_user_by_username(username)
    
    if not user_to_block:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store blocked user in data (in real implementation, would use a proper blocked list)
    if not hasattr(data_manager, 'blocked_users'):
        data_manager.blocked_users = {}
    
    if current_user["id"] not in data_manager.blocked_users:
        data_manager.blocked_users[current_user["id"]] = []
    
    data_manager.blocked_users[current_user["id"]].append(user_to_block["id"])
    return {"message": "User blocked successfully"}


@router.get("/blocked")
async def get_blocked_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get list of blocked users."""
    if not hasattr(data_manager, 'blocked_users'):
        return []
    
    blocked_ids = data_manager.blocked_users.get(current_user["id"], [])
    blocked_usernames = []
    
    for user_id in blocked_ids:
        user = next((u for u in data_manager.users if u["id"] == user_id), None)
        if user:
            blocked_usernames.append(user["username"])
    
    return blocked_usernames


@router.get("/settings")
async def get_message_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get message notification settings."""
    # Return default settings
    return {
        "email_on_new_message": True,
        "email_notifications": True,
        "push_notifications": False,
        "notification_sound": True,
        "notification_frequency": "instant"
    }


@router.put("/settings")
async def update_message_settings(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Update message notification settings."""
    # In real implementation, would persist settings
    return {
        "email_on_new_message": data.get("email_on_new_message", True),
        "email_notifications": data.get("email_notifications", True),
        "push_notifications": data.get("push_notifications", False),
        "notification_sound": data.get("notification_sound", True),
        "notification_frequency": data.get("notification_frequency", "instant"),
        "message": "Settings updated successfully"
    }


@router.get("/{message_id}")
async def get_message(message_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get a specific message."""
    message = next((m for m in data_manager.messages if m["id"] == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message["recipient_id"] != current_user["id"] and message["sender_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Add usernames
    sender = next((u for u in data_manager.users if u["id"] == message["sender_id"]), None)
    recipient = next((u for u in data_manager.users if u["id"] == message["recipient_id"]), None)
    result = message.copy()
    result["sender_username"] = sender["username"] if sender else "unknown"
    result["recipient_username"] = recipient["username"] if recipient else "unknown"
    
    return result


@router.put("/{message_id}/read", status_code=200)
async def mark_read(message_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Mark message as read."""
    message = next((m for m in data_manager.messages 
                   if m["id"] == message_id and m["recipient_id"] == current_user["id"]), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message["is_read"] = True
    message["read"] = True
    message["read_at"] = datetime.utcnow().isoformat()
    
    return message


@router.post("/{message_id}/reply", status_code=200)  # Changed from 201
async def reply_message(message_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Reply to a message."""
    original = next((m for m in data_manager.messages if m["id"] == message_id), None)
    if not original:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Ensure user has access to original message
    if original["recipient_id"] != current_user["id"] and original["sender_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine recipient of reply
    if original["sender_id"] == current_user["id"]:
        # Replying to own sent message
        recipient_id = original["recipient_id"]
    else:
        # Replying to received message
        recipient_id = original["sender_id"]
    
    recipient = next((u for u in data_manager.users if u["id"] == recipient_id), None)
    
    reply = {
        "id": str(len(data_manager.messages) + 1),
        "sender_id": current_user["id"],
        "sender_username": current_user["username"],
        "recipient_id": recipient_id,
        "recipient_username": recipient["username"] if recipient else "unknown",
        "subject": f"Re: {original['subject']}",
        "message": data.get("message", ""),
        "body": data.get("message", ""),
        "parent_message_id": message_id,  # Add parent_message_id
        "reply_to": message_id,
        "is_read": False,
        "read": False,
        "sent_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    data_manager.messages.append(reply)
    return reply


@router.delete("/{message_id}")
async def delete_message(message_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete a message."""
    message = next((m for m in data_manager.messages if m["id"] == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message["recipient_id"] != current_user["id"] and message["sender_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Message not found")
    data_manager.messages.remove(message)
    return {"message": "Message deleted successfully"}


@router.get("/thread/{message_id}")
async def get_thread(message_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get message thread."""
    # Find original message
    message = next((m for m in data_manager.messages if m["id"] == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get all messages in thread
    thread = []
    
    # Add original message
    thread.append(message)
    
    # Find all replies
    for m in data_manager.messages:
        if m.get("parent_message_id") == message_id or m.get("reply_to") == message_id:
            thread.append(m)
    
    # Add usernames to all messages
    for msg in thread:
        sender = next((u for u in data_manager.users if u["id"] == msg["sender_id"]), None)
        recipient = next((u for u in data_manager.users if u["id"] == msg["recipient_id"]), None)
        msg["sender_username"] = sender["username"] if sender else "unknown"
        msg["recipient_username"] = recipient["username"] if recipient else "unknown"
    
    return thread


@router.post("/{message_id}/attachment", status_code=200)  # Changed from 201
async def add_attachment(message_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Add attachment to message."""
    message = next((m for m in data_manager.messages if m["id"] == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message["sender_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only sender can add attachments")
    
    # Add attachment info to message
    if "attachments" not in message:
        message["attachments"] = []
    
    attachment = {
        "id": str(len(message["attachments"]) + 1),
        "filename": data.get("filename", "attachment"),
        "size": data.get("size", 0),
        "type": data.get("type", "application/octet-stream"),
        "uploaded_at": datetime.utcnow().isoformat()
    }
    
    message["attachments"].append(attachment)
    return message


@router.get("/{message_id}/permissions")
async def get_permissions(message_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get permissions for a message."""
    message = next((m for m in data_manager.messages if m["id"] == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user has access to the message
    if message["recipient_id"] != current_user["id"] and message["sender_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Message not found")
    
    permissions = []
    if message["recipient_id"] == current_user["id"] or message["sender_id"] == current_user["id"]:
        permissions.append("read")
    if message["recipient_id"] == current_user["id"]:
        permissions.append("reply")
    if message["recipient_id"] == current_user["id"] or message["sender_id"] == current_user["id"]:
        permissions.append("delete")
    
    return {"permissions": permissions}