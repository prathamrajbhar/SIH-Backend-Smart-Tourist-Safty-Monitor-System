from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    Tourist, Location, Alert, AIAssessment, 
    AlertType, AlertSeverity, AlertStatus, AISeverity
)
from app.schemas.frontend import (
    DashboardStats, TouristCard, LocationCard, AlertCard,
    SafetyMapData, TouristStatus, AlertStats, SafetyTrend,
    SystemHealth, PaginatedResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/frontend", tags=["Frontend API"])


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard statistics for frontend.
    Perfect for admin dashboard overview cards.
    """
    try:
        # Get current counts
        total_tourists = db.query(Tourist).count()
        active_tourists = db.query(Tourist).filter(Tourist.is_active == True).count()
        
        # Active alerts (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        active_alerts = db.query(Alert).filter(
            and_(
                Alert.timestamp >= yesterday,
                Alert.status == AlertStatus.ACTIVE
            )
        ).count()
        
        critical_alerts = db.query(Alert).filter(
            and_(
                Alert.timestamp >= yesterday,
                Alert.severity == AlertSeverity.CRITICAL,
                Alert.status == AlertStatus.ACTIVE
            )
        ).count()
        
        # Safety score stats
        safety_stats = db.query(
            func.avg(Tourist.safety_score).label('avg_score'),
            func.min(Tourist.safety_score).label('min_score'),
            func.max(Tourist.safety_score).label('max_score')
        ).filter(Tourist.is_active == True).first()
        
        # Recent location updates (last hour)
        recent_locations = db.query(Location).filter(
            Location.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        return DashboardStats(
            total_tourists=total_tourists,
            active_tourists=active_tourists,
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            avg_safety_score=float(safety_stats.avg_score or 0),
            min_safety_score=int(safety_stats.min_score or 0),
            max_safety_score=int(safety_stats.max_score or 100),
            recent_location_updates=recent_locations,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics"
        )


@router.get("/tourists/cards", response_model=PaginatedResponse[TouristCard])
async def get_tourist_cards(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, inactive, critical"),
    search: Optional[str] = Query(None, description="Search by name or contact"),
    db: Session = Depends(get_db)
):
    """
    Get tourist cards for frontend list/grid view.
    Includes pagination, filtering, and search.
    """
    try:
        query = db.query(Tourist)
        
        # Apply filters
        if status_filter == "active":
            query = query.filter(Tourist.is_active == True)
        elif status_filter == "inactive":
            query = query.filter(Tourist.is_active == False)
        elif status_filter == "critical":
            query = query.filter(
                and_(
                    Tourist.is_active == True,
                    Tourist.safety_score < 50
                )
            )
        
        # Apply search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Tourist.name.ilike(search_term),
                    Tourist.contact.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        tourists = query.order_by(desc(Tourist.created_at)).offset(offset).limit(size).all()
        
        # Transform to cards
        cards = []
        for tourist in tourists:
            # Get latest location
            latest_location = db.query(Location).filter(
                Location.tourist_id == tourist.id
            ).order_by(desc(Location.timestamp)).first()
            
            # Get recent alerts count
            recent_alerts = db.query(Alert).filter(
                and_(
                    Alert.tourist_id == tourist.id,
                    Alert.timestamp >= datetime.utcnow() - timedelta(hours=24),
                    Alert.status == AlertStatus.ACTIVE
                )
            ).count()
            
            cards.append(TouristCard(
                id=tourist.id,
                name=tourist.name,
                contact=tourist.contact,
                safety_score=tourist.safety_score,
                status=TouristStatus.CRITICAL if tourist.safety_score < 50 
                       else TouristStatus.WARNING if tourist.safety_score < 80 
                       else TouristStatus.SAFE,
                last_location=LocationCard(
                    latitude=float(latest_location.latitude),
                    longitude=float(latest_location.longitude),
                    timestamp=latest_location.timestamp
                ) if latest_location else None,
                recent_alerts_count=recent_alerts,
                is_active=tourist.is_active,
                last_seen=tourist.last_location_update or tourist.created_at
            ))
        
        return PaginatedResponse(
            items=cards,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except Exception as e:
        logger.error(f"Error getting tourist cards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tourist cards"
        )


@router.get("/alerts/active", response_model=List[AlertCard])
async def get_active_alerts(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db)
):
    """
    Get active alerts for real-time monitoring.
    Perfect for alert dashboards and notification systems.
    """
    try:
        query = db.query(Alert, Tourist.name.label('tourist_name')).join(
            Tourist, Alert.tourist_id == Tourist.id
        ).filter(Alert.status == AlertStatus.ACTIVE)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        alerts_data = query.order_by(desc(Alert.timestamp)).limit(limit).all()
        
        cards = []
        for alert, tourist_name in alerts_data:
            cards.append(AlertCard(
                id=alert.id,
                tourist_id=alert.tourist_id,
                tourist_name=tourist_name,
                type=alert.type,
                severity=alert.severity,
                message=alert.message,
                location=LocationCard(
                    latitude=float(alert.latitude),
                    longitude=float(alert.longitude),
                    timestamp=alert.timestamp
                ) if alert.latitude and alert.longitude else None,
                timestamp=alert.timestamp,
                auto_generated=alert.auto_generated,
                acknowledged=alert.acknowledged
            ))
        
        return cards
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active alerts"
        )


@router.get("/map/safety-data", response_model=SafetyMapData)
async def get_safety_map_data(
    bounds: Optional[str] = Query(None, description="Map bounds: lat1,lng1,lat2,lng2"),
    db: Session = Depends(get_db)
):
    """
    Get safety data for map visualization.
    Returns tourist locations, alerts, and safety zones.
    """
    try:
        # Parse bounds if provided
        lat1, lng1, lat2, lng2 = None, None, None, None
        if bounds:
            try:
                coords = [float(x.strip()) for x in bounds.split(',')]
                if len(coords) == 4:
                    lat1, lng1, lat2, lng2 = coords
            except ValueError:
                pass  # Ignore invalid bounds
        
        # Get active tourists with latest locations
        subquery = db.query(
            Location.tourist_id,
            func.max(Location.timestamp).label('max_timestamp')
        ).group_by(Location.tourist_id).subquery()
        
        locations_query = db.query(
            Location, Tourist.name, Tourist.safety_score
        ).join(
            Tourist, Location.tourist_id == Tourist.id
        ).join(
            subquery,
            and_(
                Location.tourist_id == subquery.c.tourist_id,
                Location.timestamp == subquery.c.max_timestamp
            )
        ).filter(Tourist.is_active == True)
        
        # Apply bounds filter if provided
        if all(x is not None for x in [lat1, lng1, lat2, lng2]):
            locations_query = locations_query.filter(
                and_(
                    Location.latitude.between(min(lat1, lat2), max(lat1, lat2)),
                    Location.longitude.between(min(lng1, lng2), max(lng1, lng2))
                )
            )
        
        locations_data = locations_query.all()
        
        # Get recent alerts in bounds
        alerts_query = db.query(Alert, Tourist.name.label('tourist_name')).join(
            Tourist, Alert.tourist_id == Tourist.id
        ).filter(
            and_(
                Alert.timestamp >= datetime.utcnow() - timedelta(hours=24),
                Alert.status == AlertStatus.ACTIVE,
                Alert.latitude.isnot(None),
                Alert.longitude.isnot(None)
            )
        )
        
        if all(x is not None for x in [lat1, lng1, lat2, lng2]):
            alerts_query = alerts_query.filter(
                and_(
                    Alert.latitude.between(min(lat1, lat2), max(lat1, lat2)),
                    Alert.longitude.between(min(lng1, lng2), max(lng1, lng2))
                )
            )
        
        alerts_data = alerts_query.limit(100).all()
        
        # Transform data
        tourist_locations = []
        for location, name, safety_score in locations_data:
            tourist_locations.append({
                "tourist_id": location.tourist_id,
                "name": name,
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "safety_score": safety_score,
                "status": "critical" if safety_score < 50 
                         else "warning" if safety_score < 80 
                         else "safe",
                "timestamp": location.timestamp
            })
        
        alert_locations = []
        for alert, tourist_name in alerts_data:
            alert_locations.append({
                "alert_id": alert.id,
                "tourist_name": tourist_name,
                "latitude": float(alert.latitude),
                "longitude": float(alert.longitude),
                "severity": alert.severity.value,
                "type": alert.type.value,
                "message": alert.message,
                "timestamp": alert.timestamp
            })
        
        return SafetyMapData(
            tourist_locations=tourist_locations,
            alert_locations=alert_locations,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting safety map data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch safety map data"
        )


@router.get("/analytics/trends", response_model=List[SafetyTrend])
async def get_safety_trends(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get safety trends over time for analytics dashboard.
    Returns daily aggregated safety statistics.
    """
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            # Get alerts for this day
            day_alerts = db.query(Alert).filter(
                and_(
                    Alert.timestamp >= current_date,
                    Alert.timestamp < next_date
                )
            ).all()
            
            # Get AI assessments for this day
            day_assessments = db.query(AIAssessment).filter(
                and_(
                    AIAssessment.created_at >= current_date,
                    AIAssessment.created_at < next_date
                )
            ).all()
            
            # Calculate metrics
            total_alerts = len(day_alerts)
            critical_alerts = len([a for a in day_alerts if a.severity == AlertSeverity.CRITICAL])
            panic_alerts = len([a for a in day_alerts if a.type == AlertType.PANIC])
            
            avg_safety_score = 0
            if day_assessments:
                avg_safety_score = sum(a.safety_score for a in day_assessments) / len(day_assessments)
            
            trends.append(SafetyTrend(
                date=current_date,
                total_alerts=total_alerts,
                critical_alerts=critical_alerts,
                panic_alerts=panic_alerts,
                avg_safety_score=round(avg_safety_score, 1),
                total_assessments=len(day_assessments)
            ))
        
        return trends
        
    except Exception as e:
        logger.error(f"Error getting safety trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch safety trends"
        )


@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(db: Session = Depends(get_db)):
    """
    Get system health status for monitoring dashboards.
    Includes database, AI engine, and service status.
    """
    try:
        # Test database connectivity
        db_healthy = True
        db_response_time = 0
        try:
            start_time = datetime.utcnow()
            db.execute("SELECT 1")
            db_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        except Exception:
            db_healthy = False
        
        # Check AI engine status
        ai_healthy = True
        ai_status = {}
        try:
            from app.api.ai_assessment import get_ai_engine
            engine = get_ai_engine()
            ai_status = engine.get_model_status()
        except Exception:
            ai_healthy = False
        
        # Get recent activity metrics
        recent_locations = db.query(Location).filter(
            Location.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        recent_alerts = db.query(Alert).filter(
            Alert.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        return SystemHealth(
            overall_status="healthy" if db_healthy and ai_healthy else "degraded",
            database_status="healthy" if db_healthy else "unhealthy",
            database_response_time=db_response_time,
            ai_engine_status="healthy" if ai_healthy else "unhealthy",
            ai_models_loaded=ai_status.get('models_loaded', []),
            recent_activity={
                "locations_last_5min": recent_locations,
                "alerts_last_5min": recent_alerts
            },
            last_checked=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system health"
        )


@router.get("/tourist/{tourist_id}/timeline")
async def get_tourist_timeline(
    tourist_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to fetch"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive timeline for a specific tourist.
    Includes locations, alerts, and AI assessments.
    """
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get locations
        locations = db.query(Location).filter(
            and_(
                Location.tourist_id == tourist_id,
                Location.timestamp >= cutoff_time
            )
        ).order_by(Location.timestamp).all()
        
        # Get alerts
        alerts = db.query(Alert).filter(
            and_(
                Alert.tourist_id == tourist_id,
                Alert.timestamp >= cutoff_time
            )
        ).order_by(Alert.timestamp).all()
        
        # Get AI assessments
        assessments = db.query(AIAssessment).filter(
            and_(
                AIAssessment.tourist_id == tourist_id,
                AIAssessment.created_at >= cutoff_time
            )
        ).order_by(AIAssessment.created_at).all()
        
        # Create timeline events
        timeline = []
        
        for location in locations:
            timeline.append({
                "type": "location",
                "timestamp": location.timestamp,
                "data": {
                    "latitude": float(location.latitude),
                    "longitude": float(location.longitude),
                    "speed": float(location.speed) if location.speed else None,
                    "accuracy": float(location.accuracy) if location.accuracy else None
                }
            })
        
        for alert in alerts:
            timeline.append({
                "type": "alert",
                "timestamp": alert.timestamp,
                "data": {
                    "id": alert.id,
                    "type": alert.type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "status": alert.status.value,
                    "latitude": float(alert.latitude) if alert.latitude else None,
                    "longitude": float(alert.longitude) if alert.longitude else None
                }
            })
        
        for assessment in assessments:
            timeline.append({
                "type": "ai_assessment",
                "timestamp": assessment.created_at,
                "data": {
                    "safety_score": assessment.safety_score,
                    "severity": assessment.severity.value,
                    "confidence": float(assessment.confidence_level),
                    "geofence_alert": assessment.geofence_alert,
                    "anomaly_score": float(assessment.anomaly_score) if assessment.anomaly_score else None
                }
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {
            "tourist_id": tourist_id,
            "tourist_name": tourist.name,
            "timeline": timeline,
            "summary": {
                "total_events": len(timeline),
                "locations": len(locations),
                "alerts": len(alerts),
                "ai_assessments": len(assessments),
                "time_range_hours": hours
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tourist timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tourist timeline"
        )


@router.get("/alerts/stats", response_model=AlertStats)
async def get_alert_statistics(
    days: int = Query(7, ge=1, le=30, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get detailed alert statistics for reporting.
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Get all alerts in period
        alerts = db.query(Alert).filter(Alert.timestamp >= cutoff_time).all()
        
        # Calculate statistics
        total_alerts = len(alerts)
        by_severity = {}
        by_type = {}
        by_status = {}
        
        for alert in alerts:
            # By severity
            severity = alert.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # By type
            alert_type = alert.type.value
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            
            # By status
            status_val = alert.status.value
            by_status[status_val] = by_status.get(status_val, 0) + 1
        
        # Resolution time analysis
        resolved_alerts = [a for a in alerts if a.resolved_at and a.timestamp]
        avg_resolution_time = 0
        if resolved_alerts:
            total_time = sum(
                (a.resolved_at - a.timestamp).total_seconds() 
                for a in resolved_alerts
            )
            avg_resolution_time = total_time / len(resolved_alerts) / 3600  # Convert to hours
        
        return AlertStats(
            total_alerts=total_alerts,
            by_severity=by_severity,
            by_type=by_type,
            by_status=by_status,
            resolution_rate=len(resolved_alerts) / max(total_alerts, 1) * 100,
            avg_resolution_time_hours=round(avg_resolution_time, 2),
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert statistics"
        )
