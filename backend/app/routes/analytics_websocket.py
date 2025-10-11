"""
WebSocket endpoint for real-time analytics streaming.
"""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from ..services.event_streaming import event_streaming_service
from ..utils.auth import get_current_user_ws, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time analytics."""

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}  # user_id -> websockets

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to all connections for a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()


@router.websocket("/ws/analytics")
async def analytics_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analytics updates.

    Clients should connect with authentication token in query params:
    ws://localhost:8000/api/analytics/ws/analytics?token=<jwt_token>
    """
    user_id = None

    try:
        # Get token from query params
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return

        # Verify token and get user
        # For simplicity, we'll extract user_id from token
        # In production, use proper JWT validation
        try:
            # This is a simplified authentication - in production use proper JWT validation
            from ..utils.auth import verify_token
            user_data = verify_token(token)
            user_id = user_data.get('user_id')
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return

        # Connect
        await manager.connect(websocket, user_id)

        # Subscribe to event stream
        event_queue = event_streaming_service.subscribe()

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to analytics stream",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Main event loop
        try:
            while True:
                # Check for new events from event stream
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)

                    # Only send events for this user
                    if event.get('user_id') == user_id:
                        await websocket.send_json({
                            "type": "event",
                            "data": event
                        })

                except asyncio.TimeoutError:
                    # Send heartbeat every 30 seconds
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                # Check for messages from client
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    data = json.loads(message)

                    # Handle different message types
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "subscribe":
                        # Client can request specific event types
                        event_types = data.get("event_types", [])
                        await websocket.send_json({
                            "type": "subscribed",
                            "event_types": event_types
                        })

                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received from client")
                    continue

        except WebSocketDisconnect:
            logger.info(f"Client disconnected: user {user_id}")
        finally:
            event_streaming_service.unsubscribe(event_queue)

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        if user_id:
            manager.disconnect(websocket, user_id)


@router.post("/analytics/stream/event")
async def trigger_analytics_event(
    event_type: str,
    event_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger an analytics event (for testing or manual events).
    This endpoint is primarily for internal use or testing.
    """
    from ..services.event_schemas import EventType

    try:
        # Convert string to EventType
        event_type_enum = EventType(event_type)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid event type: {event_type}"}
        )

    success, error = event_streaming_service.capture_event(
        event_type=event_type_enum,
        user_id=current_user['user_id'],
        event_data=event_data
    )

    if success:
        return {"status": "success", "message": "Event captured"}
    else:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": error}
        )
