from fastapi import APIRouter, Depends, HTTPException, status

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database import get_supabase
from app.schemas.alert import (
    AlertCreate, PanicAlertCreate, GeofenceAlertCreate, 
    AlertUpdate, AlertResponse, AlertSummary
)
from app.services.supabase_adapter import SupabaseAdapter
import logging
import httpx
import os
import json

# Enum values as constants
class AlertType:
    PANIC = "panic"
    GEOFENCE = "geofence"
    ANOMALY = "anomaly"
    TEMPORAL = "temporal"
    LOW_SAFETY_SCORE = "low_safety_score"
    SOS = "sos"
    MANUAL = "manual"

class AlertSeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    
class AlertStatus:
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Alert Management"])


# ✅ Required Endpoint: /pressSOS
@router.post("/pressSOS", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def press_sos_endpoint(
    panic_data: PanicAlertCreate,
    db = Depends(get_supabase)
):
    """
    Create an emergency SOS alert for a tourist.
    Required endpoint: /pressSOS
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Verify tourist exists
        tourist = adapter.get_by_id("tourists", panic_data.tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create SOS alert with CRITICAL severity
        alert_data = {
            "tourist_id": panic_data.tourist_id,
            "type": AlertType.PANIC,  # SOS is treated as panic
            "severity": AlertSeverity.CRITICAL,
            "message": f"🆘 EMERGENCY SOS: {panic_data.message}",
            "latitude": panic_data.latitude,
            "longitude": panic_data.longitude,
            "auto_generated": False,
            "status": AlertStatus.ACTIVE,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Insert alert
        alert = adapter.create("alerts", alert_data)
        
        # Update tourist safety score (SOS = -40, minimum score 0)
        current_score = tourist.get("safety_score", 100)
        adapter.update("tourists", panic_data.tourist_id, {
            "safety_score": max(0, current_score - 40)
        })
        
        logger.critical(f"🆘 SOS ALERT created for tourist {panic_data.tourist_id}: {panic_data.message}")
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SOS alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SOS alert"
        )


@router.post("/geofence", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_geofence_alert(
    geofence_data: GeofenceAlertCreate,
    db = Depends(get_supabase)
):
    """
    Create a geofence alert when tourist enters restricted area.
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Verify tourist exists
        tourist = adapter.get_by_id("tourists", geofence_data.tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create geofence alert
        message = geofence_data.message or f"Tourist entered restricted zone: {geofence_data.zone_name}"
        
        alert_data = {
            "tourist_id": geofence_data.tourist_id,
            "type": AlertType.GEOFENCE,
            "severity": AlertSeverity.HIGH,
            "message": message,
            "description": f"Tourist entered restricted zone: {geofence_data.zone_name}",
            "latitude": geofence_data.latitude,
            "longitude": geofence_data.longitude,
            "auto_generated": True,
            "status": AlertStatus.ACTIVE,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Insert alert
        alert = adapter.create("alerts", alert_data)
        
        # Update tourist safety score (geofence = -20, minimum score 0)
        current_score = tourist.get("safety_score", 100)
        adapter.update("tourists", geofence_data.tourist_id, {
            "safety_score": max(0, current_score - 20)
        })
        
        logger.warning(f"⚠️ Geofence alert created for tourist {geofence_data.tourist_id}: {message}")
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating geofence alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create geofence alert"
        )


@router.post("/create", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    db = Depends(get_supabase)
):
    """
    Create a general alert.
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Verify tourist exists
        tourist = adapter.get_by_id("tourists", alert_data.tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create alert record
        alert_dict = alert_data.dict()
        alert_dict["timestamp"] = datetime.utcnow().isoformat()
        
        # Insert alert
        alert = adapter.create("alerts", alert_dict)
        
        logger.info(f"Alert created: {alert['id']} for tourist {alert_data.tourist_id}")
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


# ✅ Required Endpoint: /getAlerts
@router.get("/getAlerts", response_model=List[AlertSummary])
async def get_alerts_endpoint(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_supabase)
):
    """
    Get all active alerts, optionally filtered by status.
    Required endpoint: /getAlerts
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Build query
        query = db.table("alerts").select("*")
        
        # Add filters
        if status:
            query = query.eq("status", status)
        
        if severity:
            query = query.eq("severity", severity)
            
        if alert_type:
            query = query.eq("type", alert_type)
            
        # Execute query with ordering by timestamp desc
        query = query.order("timestamp", desc=True)
        
        response = query.execute()
        alerts = response.data
        
        # Apply pagination
        start = min(skip, len(alerts))
        end = min(skip + limit, len(alerts))
        alerts = alerts[start:end]
        
        # Add tourist names
        result = []
        for alert in alerts:
            tourist = adapter.get_by_id("tourists", alert["tourist_id"])
            tourist_name = tourist["name"] if tourist else "Unknown"
            
            result.append(AlertSummary(
                id=alert["id"],
                tourist_id=alert["tourist_id"],
                tourist_name=tourist_name,
                type=alert["type"],
                message=alert["message"],
                severity=alert["severity"],
                status=alert["status"],
                timestamp=alert["timestamp"]
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts"
        )


# ✅ Required Endpoint: /resolveAlert/{id}
@router.put("/resolveAlert/{alert_id}", response_model=AlertResponse)
async def resolve_alert_endpoint(
    alert_id: int,
    db = Depends(get_supabase)
):
    """
    Mark an alert as resolved.
    Required endpoint: /resolveAlert/{id}
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Check if alert exists
        alert = adapter.get_by_id("alerts", alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
            
        # Update alert status to resolved
        resolved_alert = adapter.update("alerts", alert_id, {
            "status": AlertStatus.RESOLVED,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolved_by": "admin"  # In a real app, this would be the authenticated user
        })
        
        logger.info(f"Alert {alert_id} marked as resolved")
        return resolved_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )


@router.put("/acknowledge/{alert_id}", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db = Depends(get_supabase)
):
    """
    Mark an alert as acknowledged.
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Check if alert exists
        alert = adapter.get_by_id("alerts", alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
            
        # Update alert status to acknowledged
        acknowledged_alert = adapter.update("alerts", alert_id, {
            "status": AlertStatus.ACKNOWLEDGED,
            "acknowledged": True,
            "acknowledged_at": datetime.utcnow().isoformat(),
            "acknowledged_by": "admin"  # In a real app, this would be the authenticated user
        })
        
        logger.info(f"Alert {alert_id} acknowledged")
        return acknowledged_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@router.put("/false-alarm/{alert_id}", response_model=AlertResponse)
async def mark_false_alarm(
    alert_id: int,
    db = Depends(get_supabase)
):
    """
    Mark an alert as a false alarm.
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Check if alert exists
        alert = adapter.get_by_id("alerts", alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
            
        # Update alert status to false alarm
        false_alarm_alert = adapter.update("alerts", alert_id, {
            "status": AlertStatus.FALSE_ALARM,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolved_by": "admin",  # In a real app, this would be the authenticated user
            "resolution_notes": "Marked as false alarm"
        })
        
        logger.info(f"Alert {alert_id} marked as false alarm")
        return false_alarm_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert {alert_id} as false alarm: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark alert as false alarm"
        )