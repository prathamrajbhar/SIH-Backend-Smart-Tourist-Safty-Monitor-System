from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Alert, Tourist, AlertType, AlertSeverity, AlertStatus
from app.schemas.alert import (
    AlertCreate, PanicAlertCreate, GeofenceAlertCreate, 
    AlertUpdate, AlertResponse, AlertSummary
)
import logging
import httpx
import os
import json

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Alert Management"])


# ✅ Required Endpoint: /pressSOS
@router.post("/pressSOS", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def press_sos_endpoint(
    panic_data: PanicAlertCreate,
    db: Session = Depends(get_db)
):
    """
    Create an emergency SOS alert for a tourist.
    Required endpoint: /pressSOS
    """
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == panic_data.tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create SOS alert with CRITICAL severity
        alert = Alert(
            tourist_id=panic_data.tourist_id,
            type=AlertType.PANIC,  # SOS is treated as panic
            severity=AlertSeverity.CRITICAL,
            message=f"🆘 EMERGENCY SOS: {panic_data.message}",
            latitude=panic_data.latitude,
            longitude=panic_data.longitude,
            auto_generated=False,
            status=AlertStatus.ACTIVE
        )
        
        db.add(alert)
        
        # Update tourist safety score (SOS = -40, minimum score 0)
        tourist.safety_score = max(0, tourist.safety_score - 40)
        
        db.commit()
        db.refresh(alert)
        
        logger.critical(f"🆘 SOS ALERT created for tourist {panic_data.tourist_id}: {panic_data.message}")
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SOS alert: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SOS alert"
        )


@router.post("/alerts/geofence", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_geofence_alert(
    geofence_data: GeofenceAlertCreate,
    db: Session = Depends(get_db)
):
    """
    Create a geofence alert when tourist enters restricted area.
    Required endpoint: /alerts/geofence
    """
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == geofence_data.tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create geofence alert
        message = geofence_data.message or f"Tourist entered restricted zone: {geofence_data.zone_name}"
        
        alert = Alert(
            tourist_id=geofence_data.tourist_id,
            type=AlertType.GEOFENCE,
            severity=AlertSeverity.HIGH,
            message=message,
            description=f"Tourist entered restricted zone: {geofence_data.zone_name}",
            latitude=geofence_data.latitude,
            longitude=geofence_data.longitude,
            auto_generated=True,
            status=AlertStatus.ACTIVE
        )
        
        db.add(alert)
        
        # Update tourist safety score (risky zone = -20)
        tourist.safety_score = max(0, tourist.safety_score - 20)
        
        db.commit()
        db.refresh(alert)
        
        logger.warning(f"GEOFENCE ALERT created for tourist {geofence_data.tourist_id} - entered {geofence_data.zone_name}")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating geofence alert: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create geofence alert"
        )


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    """
    Create a generic alert.
    """
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == alert_data.tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Create alert
        alert = Alert(**alert_data.dict())
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert created: {alert.type} for tourist {alert_data.tourist_id}")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


# ✅ Required Endpoint: /getAlerts
@router.get("/getAlerts", response_model=List[AlertSummary])
async def get_alerts_endpoint(
    status: Optional[AlertStatus] = AlertStatus.ACTIVE,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get alerts with optional filtering.
    Required endpoint: /getAlerts
    """
    try:
        query = db.query(Alert, Tourist.name.label('tourist_name')).join(
            Tourist, Alert.tourist_id == Tourist.id
        )
        
        # Apply filters
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        if alert_type:
            query = query.filter(Alert.type == alert_type)
        
        # Order by most recent first
        query = query.order_by(desc(Alert.timestamp))
        
        # Apply pagination
        alerts_data = query.offset(skip).limit(limit).all()
        
        # Transform to response format
        alerts = []
        for alert, tourist_name in alerts_data:
            alert_dict = {
                "id": alert.id,
                "tourist_id": alert.tourist_id,
                "tourist_name": tourist_name,
                "type": alert.type,
                "severity": alert.severity,
                "message": alert.message,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "timestamp": alert.timestamp,
                "status": alert.status,
                "acknowledged": alert.acknowledged,
                "resolved_at": alert.resolved_at
            }
            alerts.append(alert_dict)
        
        logger.info(f"Retrieved {len(alerts)} alerts")
        return alerts
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


# Legacy endpoint for backward compatibility
@router.get("/", response_model=List[AlertSummary])
async def get_alerts(
    status: Optional[AlertStatus] = AlertStatus.ACTIVE,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get alerts (legacy endpoint)"""
    return await get_alerts_endpoint(status, severity, alert_type, skip, limit, db)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific alert.
    Required endpoint: GET /alerts/{alert_id}
    Used By: AlertsScreen for showing alert details
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert"
        )


@router.put("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    resolution_data: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Resolve an alert.
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update alert status
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        if resolution_data.resolved_by:
            alert.resolved_by = resolution_data.resolved_by
        if resolution_data.resolution_notes:
            alert.resolution_notes = resolution_data.resolution_notes
        
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert {alert_id} resolved by {resolution_data.resolved_by}")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    acknowledgment_data: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Mark alerts as read/acknowledged by the user.
    Required endpoint: PUT /alerts/{alert_id}/acknowledge
    Used By: AlertsScreen for interactive alert management
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update acknowledgment status
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.status = AlertStatus.ACKNOWLEDGED
        
        if acknowledgment_data.acknowledged_by:
            alert.acknowledged_by = acknowledgment_data.acknowledged_by
        
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledgment_data.acknowledged_by}")
        
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


@router.post("/forwardAlert/{alert_id}", response_model=dict)
async def forward_panic_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Forward panic alert to emergency response systems.
    Sends alert to police, emergency services, and other response systems.
    """
    try:
        # Get the panic alert
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.type.in_([AlertType.PANIC, AlertType.SOS])
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Panic/SOS alert not found"
            )
        
        # Get tourist info
        tourist = db.query(Tourist).filter(Tourist.id == alert.tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Prepare emergency response data
        emergency_data = {
            "alert_id": alert.id,
            "emergency_type": "TOURIST_PANIC_SOS",
            "severity": alert.severity.value,
            "timestamp": alert.timestamp.isoformat(),
            "location": {
                "latitude": alert.latitude,
                "longitude": alert.longitude
            },
            "tourist": {
                "id": tourist.id,
                "name": tourist.name,
                "contact": tourist.contact,
                "emergency_contact": tourist.emergency_contact
            },
            "message": alert.message,
            "priority": "CRITICAL"
        }
        
        # Emergency response URL (configurable via environment)
        emergency_url = os.getenv("EMERGENCY_RESPONSE_URL", "http://emergency-api.example.com/alert")
        
        # Send to emergency response systems
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    emergency_url,
                    json=emergency_data,
                    headers={
                        "Content-Type": "application/json",
                        "X-Source": "Tourist-Safety-System"
                    }
                )
                
                if response.status_code == 200:
                    # Mark alert as forwarded
                    alert.acknowledged = True
                    alert.acknowledged_by = "Emergency Response System"
                    alert.acknowledged_at = datetime.utcnow()
                    db.commit()
                    
                    logger.critical(f"� Alert {alert_id} forwarded to emergency response systems successfully")
                    
                    return {
                        "success": True,
                        "message": "Alert forwarded to emergency response systems",
                        "alert_id": alert_id,
                        "response_status": response.status_code
                    }
                else:
                    logger.error(f"Emergency response system returned status {response.status_code}")
                    return {
                        "success": False,
                        "message": f"Emergency system error: {response.status_code}",
                        "alert_id": alert_id
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout forwarding alert {alert_id} to emergency systems")
            return {
                "success": False,
                "message": "Timeout connecting to emergency response systems",
                "alert_id": alert_id
            }
        except Exception as e:
            logger.error(f"Error forwarding to emergency systems: {e}")
            return {
                "success": False,
                "message": f"Emergency system connection error: {str(e)}",
                "alert_id": alert_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in alert forwarding endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to forward alert to emergency systems"
        )


@router.get("/panicAlertsCount", response_model=dict)
async def get_panic_alerts_count(
    db: Session = Depends(get_db)
):
    """
    Get total count of panic alerts for dashboard statistics.
    Required endpoint: GET /alerts/panicAlertsCount
    Used By: DashboardScreen for showing alert statistics
    """
    try:
        # Count total panic/SOS alerts
        total_count = db.query(Alert).filter(
            Alert.type.in_([AlertType.PANIC, AlertType.SOS])
        ).count()
        
        # Count by status
        active_count = db.query(Alert).filter(
            Alert.type.in_([AlertType.PANIC, AlertType.SOS]),
            Alert.status == AlertStatus.ACTIVE
        ).count()
        
        resolved_count = db.query(Alert).filter(
            Alert.type.in_([AlertType.PANIC, AlertType.SOS]),
            Alert.status == AlertStatus.RESOLVED
        ).count()
        
        logger.info(f"Retrieved panic alert counts: Total={total_count}, Active={active_count}")
        
        # Return in the exact format required by the mobile app
        return {
            "total_panic_alerts": total_count,
            "active_panic_alerts": active_count,
            "resolved_panic_alerts": resolved_count
        }
        
    except Exception as e:
        logger.error(f"Error getting panic alerts count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get panic alerts count"
        )