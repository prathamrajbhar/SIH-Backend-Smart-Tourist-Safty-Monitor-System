from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
import logging
from app.database import get_db
from app.models import Tourist, Location, Alert, AlertStatus, AlertSeverity
from app.schemas.frontend import WSMessage, LiveUpdate, NotificationPayload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/realtime", tags=["Real-time API"])


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = {
            "channels": ["all"],
            "tourist_ids": None,
            "filters": {}
        }
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], channel: str = "all"):
        """Broadcast message to all subscribed connections."""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, default=str)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                subscription = self.subscriptions.get(connection, {})
                channels = subscription.get("channels", ["all"])
                
                # Check if connection is subscribed to this channel
                if channel in channels or "all" in channels:
                    # Apply filters if any
                    if self._message_matches_filters(message, subscription):
                        await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    def _message_matches_filters(self, message: Dict[str, Any], subscription: Dict[str, Any]) -> bool:
        """Check if message matches subscription filters."""
        tourist_ids = subscription.get("tourist_ids")
        if tourist_ids and message.get("data", {}).get("tourist_id") not in tourist_ids:
            return False
        
        filters = subscription.get("filters", {})
        if filters.get("severity") and message.get("data", {}).get("severity") != filters["severity"]:
            return False
        
        return True
    
    async def update_subscription(self, websocket: WebSocket, subscription: Dict[str, Any]):
        """Update subscription preferences for a connection."""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(subscription)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    Clients can subscribe to different channels and receive live updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client (subscription updates, heartbeat, etc.)
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    await manager.update_subscription(websocket, message.get("data", {}))
                elif message.get("type") == "heartbeat":
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from WebSocket client")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.post("/broadcast/alert")
async def broadcast_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Broadcast an alert to all connected clients.
    Called internally when new alerts are created.
    """
    try:
        # Get alert details
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Get tourist info
        tourist = db.query(Tourist).filter(Tourist.id == alert.tourist_id).first()
        
        # Create broadcast message
        message = {
            "type": "new_alert",
            "channel": "alerts",
            "data": {
                "alert_id": alert.id,
                "tourist_id": alert.tourist_id,
                "tourist_name": tourist.name if tourist else "Unknown",
                "type": alert.type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "latitude": float(alert.latitude) if alert.latitude else None,
                "longitude": float(alert.longitude) if alert.longitude else None,
                "timestamp": alert.timestamp.isoformat(),
                "auto_generated": alert.auto_generated
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all connected clients
        await manager.broadcast(message, "alerts")
        
        return {"success": True, "message": "Alert broadcasted", "connections": len(manager.active_connections)}
        
    except Exception as e:
        logger.error(f"Error broadcasting alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast alert"
        )


@router.post("/broadcast/location")
async def broadcast_location_update(
    tourist_id: int,
    location_id: int,
    db: Session = Depends(get_db)
):
    """
    Broadcast location update to all connected clients.
    Called internally when new locations are received.
    """
    try:
        # Get location and tourist details
        location = db.query(Location).filter(Location.id == location_id).first()
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        
        if not location or not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location or tourist not found"
            )
        
        # Create broadcast message
        message = {
            "type": "location_update",
            "channel": "locations",
            "data": {
                "tourist_id": tourist_id,
                "tourist_name": tourist.name,
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "speed": float(location.speed) if location.speed else None,
                "accuracy": float(location.accuracy) if location.accuracy else None,
                "safety_score": tourist.safety_score,
                "timestamp": location.timestamp.isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all connected clients
        await manager.broadcast(message, "locations")
        
        return {"success": True, "message": "Location update broadcasted"}
        
    except Exception as e:
        logger.error(f"Error broadcasting location update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast location update"
        )


@router.get("/live/active-alerts")
async def get_live_active_alerts(
    db: Session = Depends(get_db)
):
    """
    Get currently active alerts for live monitoring.
    Returns simplified data optimized for real-time dashboards.
    """
    try:
        alerts = db.query(Alert).filter(
            Alert.status == AlertStatus.ACTIVE
        ).order_by(desc(Alert.timestamp)).limit(20).all()
        
        live_alerts = []
        for alert in alerts:
            tourist = db.query(Tourist).filter(Tourist.id == alert.tourist_id).first()
            
            live_alerts.append({
                "id": alert.id,
                "tourist_id": alert.tourist_id,
                "tourist_name": tourist.name if tourist else "Unknown",
                "type": alert.type.value,
                "severity": alert.severity.value,
                "message": alert.message[:100] + "..." if len(alert.message) > 100 else alert.message,
                "location": {
                    "latitude": float(alert.latitude),
                    "longitude": float(alert.longitude)
                } if alert.latitude and alert.longitude else None,
                "timestamp": alert.timestamp.isoformat(),
                "age_minutes": int((datetime.utcnow() - alert.timestamp).total_seconds() / 60)
            })
        
        return {
            "alerts": live_alerts,
            "total_active": len(live_alerts),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting live active alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live active alerts"
        )


@router.get("/live/tourist-positions")
async def get_live_tourist_positions(
    db: Session = Depends(get_db)
):
    """
    Get current positions of all active tourists.
    Optimized for real-time map updates.
    """
    try:
        # Get latest location for each active tourist
        from sqlalchemy import func
        
        subquery = db.query(
            Location.tourist_id,
            func.max(Location.timestamp).label('max_timestamp')
        ).group_by(Location.tourist_id).subquery()
        
        positions = db.query(
            Location.tourist_id,
            Location.latitude,
            Location.longitude,
            Location.timestamp,
            Tourist.name,
            Tourist.safety_score
        ).join(
            Tourist, Location.tourist_id == Tourist.id
        ).join(
            subquery,
            and_(
                Location.tourist_id == subquery.c.tourist_id,
                Location.timestamp == subquery.c.max_timestamp
            )
        ).filter(
            Tourist.is_active == True
        ).all()
        
        live_positions = []
        for pos in positions:
            status = "safe"
            if pos.safety_score < 50:
                status = "critical"
            elif pos.safety_score < 80:
                status = "warning"
            
            live_positions.append({
                "tourist_id": pos.tourist_id,
                "name": pos.name,
                "latitude": float(pos.latitude),
                "longitude": float(pos.longitude),
                "safety_score": pos.safety_score,
                "status": status,
                "last_update": pos.timestamp.isoformat(),
                "age_minutes": int((datetime.utcnow() - pos.timestamp).total_seconds() / 60)
            })
        
        return {
            "positions": live_positions,
            "total_tourists": len(live_positions),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting live tourist positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live tourist positions"
        )


@router.get("/live/system-metrics")
async def get_live_system_metrics(
    db: Session = Depends(get_db)
):
    """
    Get real-time system metrics for monitoring dashboards.
    """
    try:
        now = datetime.utcnow()
        
        # Calculate metrics for different time windows
        metrics = {
            "last_minute": {
                "new_locations": 0,
                "new_alerts": 0,
                "active_tourists": 0
            },
            "last_5_minutes": {
                "new_locations": 0,
                "new_alerts": 0,
                "critical_alerts": 0
            },
            "last_hour": {
                "new_locations": 0,
                "new_alerts": 0,
                "panic_alerts": 0
            }
        }
        
        # Last minute
        minute_ago = now - timedelta(minutes=1)
        metrics["last_minute"]["new_locations"] = db.query(Location).filter(
            Location.timestamp >= minute_ago
        ).count()
        metrics["last_minute"]["new_alerts"] = db.query(Alert).filter(
            Alert.timestamp >= minute_ago
        ).count()
        
        # Last 5 minutes
        five_min_ago = now - timedelta(minutes=5)
        metrics["last_5_minutes"]["new_locations"] = db.query(Location).filter(
            Location.timestamp >= five_min_ago
        ).count()
        metrics["last_5_minutes"]["new_alerts"] = db.query(Alert).filter(
            Alert.timestamp >= five_min_ago
        ).count()
        metrics["last_5_minutes"]["critical_alerts"] = db.query(Alert).filter(
            and_(
                Alert.timestamp >= five_min_ago,
                Alert.severity == AlertSeverity.CRITICAL
            )
        ).count()
        
        # Last hour
        hour_ago = now - timedelta(hours=1)
        metrics["last_hour"]["new_locations"] = db.query(Location).filter(
            Location.timestamp >= hour_ago
        ).count()
        metrics["last_hour"]["new_alerts"] = db.query(Alert).filter(
            Alert.timestamp >= hour_ago
        ).count()
        
        # Active tourists (updated in last 30 minutes)
        thirty_min_ago = now - timedelta(minutes=30)
        active_tourists = db.query(Tourist).filter(
            and_(
                Tourist.is_active == True,
                Tourist.last_location_update >= thirty_min_ago
            )
        ).count()
        
        metrics["active_tourists_30min"] = active_tourists
        
        # WebSocket connections
        metrics["websocket_connections"] = len(manager.active_connections)
        
        return {
            "metrics": metrics,
            "timestamp": now.isoformat(),
            "system_status": "healthy"  # Could be enhanced with actual health checks
        }
        
    except Exception as e:
        logger.error(f"Error getting live system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch live system metrics"
        )


# Background task to send periodic updates
async def periodic_update_broadcaster():
    """
    Background task that sends periodic updates to connected clients.
    This can be called from the main application startup.
    """
    while True:
        try:
            if manager.active_connections:
                # Send heartbeat to all connections
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "connections": len(manager.active_connections)
                }
                await manager.broadcast(heartbeat_message, "system")
            
            # Wait 30 seconds before next heartbeat
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in periodic update broadcaster: {e}")
            await asyncio.sleep(60)  # Wait longer on error


# Helper function to get connection manager (for use in other modules)
def get_connection_manager():
    return manager
