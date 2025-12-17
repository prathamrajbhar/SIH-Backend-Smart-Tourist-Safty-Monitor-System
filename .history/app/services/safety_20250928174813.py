from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from app.models import Tourist, Location, Alert, RestrictedZone, SafeZone, AlertType, AlertSeverity
from shapely.geometry import Point, Polygon
import logging

logger = logging.getLogger(__name__)


class SafetyService:
    """
    Service for calculating safety scores and managing safety-related operations.
    """
    
    # Safety score modifiers
    PANIC_PENALTY = -40
    RISKY_ZONE_PENALTY = -20
    SAFE_DURATION_BONUS = +10  # Per hour
    GEOFENCE_VIOLATION_PENALTY = -25
    INACTIVITY_PENALTY = -5  # Per hour of inactivity
    
    def __init__(self, db: Session):
        self.db = db

    def calculate_safety_score(self, tourist_id: int) -> Dict[str, Any]:
        """
        Calculate and update the safety score for a tourist based on recent activity.
        
        Returns:
            Dict containing updated safety score, reasons for changes, and recommendations.
        """
        try:
            tourist = self.db.query(Tourist).filter(Tourist.id == tourist_id).first()
            if not tourist:
                raise ValueError("Tourist not found")
            
            initial_score = tourist.safety_score
            current_score = initial_score
            changes = []
            recommendations = []
            
            # Check recent alerts (last 24 hours)
            recent_alerts = self.db.query(Alert).filter(
                Alert.tourist_id == tourist_id,
                Alert.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            for alert in recent_alerts:
                if alert.type == AlertType.PANIC:
                    current_score += self.PANIC_PENALTY
                    changes.append(f"Panic alert: {self.PANIC_PENALTY}")
                elif alert.type == AlertType.GEOFENCE:
                    current_score += self.GEOFENCE_VIOLATION_PENALTY
                    changes.append(f"Geofence violation: {self.GEOFENCE_VIOLATION_PENALTY}")
            
            # Check recent location activity
            last_location = self.db.query(Location).filter(
                Location.tourist_id == tourist_id
            ).order_by(Location.timestamp.desc()).first()
            
            if last_location:
                time_since_update = datetime.utcnow() - last_location.timestamp
                
                # Check for prolonged inactivity (no location updates)
                if time_since_update > timedelta(hours=2):
                    hours_inactive = int(time_since_update.total_seconds() / 3600)
                    penalty = self.INACTIVITY_PENALTY * hours_inactive
                    current_score += penalty
                    changes.append(f"Inactivity penalty ({hours_inactive}h): {penalty}")
                    recommendations.append("Contact tourist - no recent location updates")
                
                # Check if in safe/restricted zones
                zone_check = self.check_location_safety(
                    float(last_location.latitude), 
                    float(last_location.longitude)
                )
                
                if zone_check["in_restricted_zone"]:
                    current_score += self.RISKY_ZONE_PENALTY
                    changes.append(f"In restricted zone: {self.RISKY_ZONE_PENALTY}")
                    recommendations.append(f"Tourist in restricted area: {zone_check['restricted_zone_name']}")
                
                if zone_check["in_safe_zone"]:
                    # Bonus for staying in safe areas
                    safe_duration_hours = self.calculate_safe_zone_duration(tourist_id)
                    if safe_duration_hours >= 1:
                        bonus = min(self.SAFE_DURATION_BONUS * int(safe_duration_hours), 20)  # Cap at +20
                        current_score += bonus
                        changes.append(f"Safe zone bonus ({int(safe_duration_hours)}h): +{bonus}")
            
            # Ensure score stays within bounds (0-100)
            current_score = max(0, min(100, current_score))
            
            # Update tourist safety score
            tourist.safety_score = current_score
            self.db.commit()
            
            # Determine severity and actions
            severity = self.get_safety_severity(current_score)
            if current_score < 50:
                recommendations.append("CRITICAL: Immediate intervention required")
            elif current_score < 70:
                recommendations.append("WARNING: Monitor closely")
            
            result = {
                "tourist_id": tourist_id,
                "previous_score": initial_score,
                "current_score": current_score,
                "score_change": current_score - initial_score,
                "severity": severity,
                "changes": changes,
                "recommendations": recommendations,
                "last_updated": datetime.utcnow()
            }
            
            logger.info(f"Safety score updated for tourist {tourist_id}: {initial_score} -> {current_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating safety score for tourist {tourist_id}: {e}")
            raise

    def check_location_safety(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Check if a location is in safe or restricted zones.
        """
        try:
            point = Point(longitude, latitude)  # Note: longitude, latitude order for Point
            
            # Check restricted zones
            restricted_zones = self.db.query(RestrictedZone).filter(
                RestrictedZone.is_active == True
            ).all()
            
            in_restricted_zone = False
            restricted_zone_name = None
            
            for zone in restricted_zones:
                try:
                    # Convert GeoJSON coordinates to Shapely Polygon
                    coordinates = zone.coordinates.get('coordinates', [])
                    if coordinates and len(coordinates) > 0:
                        polygon = Polygon(coordinates[0])  # Assuming first ring is outer boundary
                        if polygon.contains(point):
                            in_restricted_zone = True
                            restricted_zone_name = zone.name
                            break
                except Exception as e:
                    logger.warning(f"Error checking restricted zone {zone.id}: {e}")
                    continue
            
            # Check safe zones
            safe_zones = self.db.query(SafeZone).filter(
                SafeZone.is_active == True
            ).all()
            
            in_safe_zone = False
            safe_zone_name = None
            
            for zone in safe_zones:
                try:
                    coordinates = zone.coordinates.get('coordinates', [])
                    if coordinates and len(coordinates) > 0:
                        polygon = Polygon(coordinates[0])
                        if polygon.contains(point):
                            in_safe_zone = True
                            safe_zone_name = zone.name
                            break
                except Exception as e:
                    logger.warning(f"Error checking safe zone {zone.id}: {e}")
                    continue
            
            return {
                "latitude": latitude,
                "longitude": longitude,
                "in_restricted_zone": in_restricted_zone,
                "restricted_zone_name": restricted_zone_name,
                "in_safe_zone": in_safe_zone,
                "safe_zone_name": safe_zone_name
            }
            
        except Exception as e:
            logger.error(f"Error checking location safety: {e}")
            return {
                "latitude": latitude,
                "longitude": longitude,
                "in_restricted_zone": False,
                "restricted_zone_name": None,
                "in_safe_zone": False,
                "safe_zone_name": None,
                "error": str(e)
            }

    def calculate_safe_zone_duration(self, tourist_id: int) -> float:
        """
        Calculate how long a tourist has been in safe zones (in hours).
        """
        try:
            # Get recent locations (last 24 hours)
            recent_locations = self.db.query(Location).filter(
                Location.tourist_id == tourist_id,
                Location.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(Location.timestamp.desc()).all()
            
            if not recent_locations:
                return 0.0
            
            safe_duration = 0.0
            
            for i, location in enumerate(recent_locations):
                zone_check = self.check_location_safety(
                    float(location.latitude), 
                    float(location.longitude)
                )
                
                if zone_check["in_safe_zone"]:
                    # Calculate duration at this location
                    if i < len(recent_locations) - 1:
                        # Time between this location and the next (older) one
                        time_diff = recent_locations[i + 1].timestamp - location.timestamp
                        safe_duration += time_diff.total_seconds() / 3600  # Convert to hours
                    else:
                        # For the oldest location, assume 1 hour if in safe zone
                        safe_duration += 1.0
            
            return safe_duration
            
        except Exception as e:
            logger.error(f"Error calculating safe zone duration for tourist {tourist_id}: {e}")
            return 0.0

    def get_safety_severity(self, safety_score: int) -> str:
        """
        Determine safety severity based on score.
        """
        if safety_score >= 80:
            return "SAFE"
        elif safety_score >= 50:
            return "WARNING"
        else:
            return "CRITICAL"

    def trigger_automatic_assessment(self, tourist_id: int, location_id: int = None):
        """
        Trigger automatic safety assessment and create alerts if necessary.
        """
        try:
            assessment = self.calculate_safety_score(tourist_id)
            
            # Create alert if score is critical
            if assessment["current_score"] < 50:
                alert = Alert(
                    tourist_id=tourist_id,
                    type=AlertType.LOW_SAFETY_SCORE,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Critical safety score: {assessment['current_score']}",
                    description=f"Safety assessment triggered automatic alert. Reasons: {', '.join(assessment['changes'])}",
                    auto_generated=True
                )
                self.db.add(alert)
                self.db.commit()
                
                logger.warning(f"Automatic CRITICAL alert created for tourist {tourist_id}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in automatic assessment for tourist {tourist_id}: {e}")
            raise