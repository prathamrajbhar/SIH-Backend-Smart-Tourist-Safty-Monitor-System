"""
Alert Management API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging
from datetime import datetime

from app.database import get_supabase
from app.schemas.alert import (
    AlertCreate, PanicAlertCreate, GeofenceAlertCreate,
    AlertUpdate, AlertResponse, AlertSummary
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Alert Management"])


# ✅ Required Endpoint: /pressSOS
@router.post("/pressSOS", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def press_sos_endpoint(panic_data: PanicAlertCreate):
    """
    Create an emergency SOS alert for a tourist.
    Required endpoint: /pressSOS
    """
    try:
        supabase = get_supabase()
        
        # Verify tourist exists
        tourist_result = supabase.table("tourists").select("*").eq("id", panic_data.tourist_id).execute()
        if not tourist_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create SOS alert with CRITICAL severity
        alert = {
            "tourist_id": panic_data.tourist_id,
            "type": "panic",  # SOS is treated as panic
            "severity": "CRITICAL",
            "message": f"🆘 EMERGENCY SOS: {panic_data.message}",
            "latitude": panic_data.latitude,
            "longitude": panic_data.longitude,
            "auto_generated": False,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Insert alert
        result = supabase.table("alerts").insert(alert).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create alert"
            )
        
        db_alert = result.data[0]
        
        # Update tourist safety score (significant reduction for SOS)
        tourist = tourist_result.data[0]
        current_score = tourist.get("safety_score", 100)
        new_score = max(0, current_score - 40)  # Reduce by 40 points for SOS
        
        supabase.table("tourists").update({
            "safety_score": new_score
        }).eq("id", panic_data.tourist_id).execute()
        
        logger.info(f"SOS Alert created for tourist {panic_data.tourist_id} - Alert ID: {db_alert['id']}")
        
        # In a real system, we would trigger notifications here
        
        return db_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SOS alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SOS alert"
        )


@router.post("/api/v1/alerts/panic", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_panic_alert(panic_data: PanicAlertCreate):
    """
    Create a panic alert (API v1 endpoint)
    """
    return await press_sos_endpoint(panic_data)


@router.post("/api/v1/alerts/geofence", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_geofence_alert(geofence_data: GeofenceAlertCreate):
    """
    Create a geofence violation alert
    """
    try:
        supabase = get_supabase()
        
        # Verify tourist exists
        tourist_result = supabase.table("tourists").select("*").eq("id", geofence_data.tourist_id).execute()
        if not tourist_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create geofence alert
        alert = {
            "tourist_id": geofence_data.tourist_id,
            "type": "geofence",
            "severity": geofence_data.severity,
            "message": geofence_data.message,
            "latitude": geofence_data.latitude,
            "longitude": geofence_data.longitude,
            "auto_generated": geofence_data.auto_generated,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Insert alert
        result = supabase.table("alerts").insert(alert).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create alert"
            )
        
        db_alert = result.data[0]
        
        # Update tourist safety score (reduction for geofence violation)
        tourist = tourist_result.data[0]
        current_score = tourist.get("safety_score", 100)
        new_score = max(0, current_score - 20)  # Reduce by 20 points for geofence
        
        supabase.table("tourists").update({
            "safety_score": new_score
        }).eq("id", geofence_data.tourist_id).execute()
        
        logger.info(f"Geofence Alert created for tourist {geofence_data.tourist_id} - Alert ID: {db_alert['id']}")
        
        return db_alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating geofence alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create geofence alert"
        )


# ✅ Required Endpoint: /getAlerts
@router.get("/getAlerts", response_model=List[AlertResponse])
async def get_alerts_endpoint(active_only: bool = True):
    """
    Get all alerts, optionally filtering for active ones only.
    Required endpoint: /getAlerts
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("alerts").select("*")
        
        if active_only:
            query = query.eq("status", "active")
            
        # Order by timestamp descending (most recent first)
        result = query.order("timestamp", desc=True).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.get("/api/v1/alerts", response_model=List[AlertResponse])
async def get_alerts(
    active_only: bool = True,
    tourist_id: Optional[int] = None
):
    """
    Get alerts with optional filtering (API v1 endpoint)
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("alerts").select("*")
        
        if active_only:
            query = query.eq("status", "active")
            
        if tourist_id is not None:
            query = query.eq("tourist_id", tourist_id)
            
        # Order by timestamp descending (most recent first)
        result = query.order("timestamp", desc=True).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.put("/api/v1/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: int):
    """
    Resolve an active alert
    """
    try:
        supabase = get_supabase()
        
        # Check if alert exists
        alert_result = supabase.table("alerts").select("*").eq("id", alert_id).execute()
        
        if not alert_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update alert status
        result = supabase.table("alerts").update({
            "status": "resolved"
        }).eq("id", alert_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update alert"
            )
        
        logger.info(f"Alert {alert_id} resolved")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )