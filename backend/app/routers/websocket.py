"""
WebSocket Router - Real-time Metrics
Expert Recommendation Implementation
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, RemixNode

router = APIRouter()

# Store active connections per user
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time metrics"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"✅ WebSocket connected: {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"❌ WebSocket disconnected: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to all connections for a specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/metrics/{user_id}")
async def websocket_metrics(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time metrics updates.
    
    Sends periodic updates about:
    - Total views across user's nodes
    - K-Points balance
    - Recent transactions
    - Streak status
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Initial data fetch and send (from the database)
        async with asyncio.timeout(30):  # Handle database connection issues
            async for session in get_db():
                initial_data = await fetch_user_metrics(session, user_id)
                await websocket.send_json({
                    "type": "initial",
                    "data": initial_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for any message from client (heartbeat)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )
                
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif data == "refresh":
                    # Client requested refresh
                    async for session in get_db():
                        fresh_data = await fetch_user_metrics(session, user_id)
                        await websocket.send_json({
                            "type": "refresh",
                            "data": fresh_data,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        break
                        
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({
                    "type": "keepalive",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"⚠️ WebSocket error for {user_id}: {e}")
        manager.disconnect(websocket, user_id)


async def fetch_user_metrics(db: AsyncSession, user_id: str) -> dict:
    """Fetch current metrics for a user"""
    import uuid
    
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return {
            "error": "Invalid user ID",
            "total_views": 0,
            "k_points": 0,
            "pending_royalty": 0,
            "node_count": 0,
            "today_views": 0,
            "today_revenue": 0
        }
    
    # Get user
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    
    if not user:
        return {
            "error": "User not found",
            "total_views": 0,
            "k_points": 0,
            "pending_royalty": 0,
            "node_count": 0,
            "today_views": 0,
            "today_revenue": 0
        }
    
    # Get aggregate stats from user's nodes
    from sqlalchemy import func
    nodes_result = await db.execute(
        select(
            func.coalesce(func.sum(RemixNode.view_count), 0).label("total_views"),
            func.count(RemixNode.id).label("node_count")
        ).where(RemixNode.created_by == uid)
    )
    stats = nodes_result.one()
    
    return {
        "user_id": user_id,
        "total_views": int(stats.total_views),
        "k_points": user.k_points,
        "pending_royalty": user.pending_royalty,
        "total_royalty_received": user.total_royalty_received,
        "node_count": int(stats.node_count),
        # Simulated "today" stats (would need actual time-based tracking)
        "today_views": int(stats.total_views) // 10,  # Placeholder
        "today_revenue": round(float(user.pending_royalty) * 0.01, 2)  # Placeholder
    }


# Helper function to broadcast metrics updates (can be called from other parts of the app)
async def broadcast_metrics_update(user_id: str, update_type: str, data: dict):
    """
    Broadcast a metrics update to a specific user.
    Call this from other parts of the app when metrics change.
    
    Example usage:
        await broadcast_metrics_update(
            user_id="123", 
            update_type="view_increment",
            data={"node_id": "xyz", "new_views": 100}
        )
    """
    await manager.send_personal_message({
        "type": update_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }, user_id)
