from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional, Union
from supabase import Client
from app.models import Tourist, Location, Alert, RestrictedZone, SafeZone, AlertType, AlertSeverity
from shapely.geometry import Point, Polygon
from app.services.supabase_utils import (
    safe_supabase_query, safe_supabase_get, 
    safe_supabase_insert, safe_supabase_update, 
    SupabaseError
)
import logging
import json

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
    
    def __init__(self, db: Client):
        self.db = db

    @safe_supabase_query
    def calculate_safety_score(self, tourist_id: int) -> Dict[str, Any]:
        """
        Calculate and update the safety score for a tourist based on recent activity.
        
        Returns:
            Dict containing updated safety score, reasons for changes, and recommendations.
        """
        try:
            # Get tourist data from Supabase using safe utility
            try:
                tourist = safe_supabase_get(self.db, "tourists", tourist_id)
            except SupabaseError as e:
                logger.error(f"Failed to get tourist {tourist_id}: {str(e)}")
                raise ValueError(f"Tourist not found or database error: {str(e)}")
            
            initial_score = tourist.get('safety_score', 100)
            current_score = initial_score
            changes = []
            recommendations = []
            
            # Check recent alerts (last 24 hours)
            twenty_four_hours_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            recent_alerts_response = self.db.table("alerts").select("*") \
                .eq("tourist_id", tourist_id) \
                .gte("timestamp", twenty_four_hours_ago) \
                .execute()
                
            recent_alerts = recent_alerts_response.data
            
            for alert in recent_alerts:
                if alert.get('type') == AlertType.PANIC.value:
                    current_score += self.PANIC_PENALTY
                    changes.append(f"Panic alert: {self.PANIC_PENALTY}")
                elif alert.get('type') == AlertType.GEOFENCE.value:
                    current_score += self.GEOFENCE_VIOLATION_PENALTY
                    changes.append(f"Geofence violation: {self.GEOFENCE_VIOLATION_PENALTY}")
            
            # Check recent location activity
            last_location_response = self.db.table("locations").select("*") \
                .eq("tourist_id", tourist_id) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .execute()
                
            last_location = last_location_response.data[0] if last_location_response.data else None
            
            if last_location:
                last_timestamp = datetime.fromisoformat(last_location.get('timestamp').replace('Z', '+00:00'))
                time_since_update = datetime.utcnow() - last_timestamp
                
                # Check for prolonged inactivity (no location updates)
                if time_since_update > timedelta(hours=2):
                    hours_inactive = int(time_since_update.total_seconds() / 3600)
                    penalty = self.INACTIVITY_PENALTY * hours_inactive
                    current_score += penalty
                    changes.append(f"Inactivity penalty ({hours_inactive}h): {penalty}")
                    recommendations.append("Contact tourist - no recent location updates")
                
                # Check if in safe/restricted zones
                zone_check = self.check_location_safety(
                    float(last_location.get('latitude')), 
                    float(last_location.get('longitude'))
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
            
            # Update tourist safety score using safe utility
            update_data = {
                "safety_score": current_score, 
                "updated_at": datetime.utcnow().isoformat(),
                "last_location_update": datetime.utcnow().isoformat() if last_location else None
            }
            safe_supabase_update(self.db, "tourists", update_data, tourist_id)
            
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
            restricted_zones_response = self.db.table("restricted_zones").select("*") \
                .eq("is_active", True) \
                .execute()
            
            restricted_zones = restricted_zones_response.data
            
            in_restricted_zone = False
            restricted_zone_name = None
            
            for zone in restricted_zones:
                try:
                    # Convert GeoJSON coordinates to Shapely Polygon
                    coordinates = zone.get('coordinates', {}).get('coordinates', [])
                    if coordinates and len(coordinates) > 0:
                        polygon = Polygon(coordinates[0])  # Assuming first ring is outer boundary
                        if polygon.contains(point):
                            in_restricted_zone = True
                            restricted_zone_name = zone.get('name')
                            break
                except Exception as e:
                    logger.warning(f"Error checking restricted zone {zone.get('id')}: {e}")
                    continue
            
            # Check safe zones
            safe_zones_response = self.db.table("safe_zones").select("*") \
                .eq("is_active", True) \
                .execute()
            
            safe_zones = safe_zones_response.data
            
            in_safe_zone = False
            safe_zone_name = None
            
            for zone in safe_zones:
                try:
                    coordinates = zone.get('coordinates', {}).get('coordinates', [])
                    if coordinates and len(coordinates) > 0:
                        polygon = Polygon(coordinates[0])
                        if polygon.contains(point):
                            in_safe_zone = True
                            safe_zone_name = zone.get('name')
                            break
                except Exception as e:
                    logger.warning(f"Error checking safe zone {zone.get('id')}: {e}")
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
            twenty_four_hours_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            recent_locations_response = self.db.table("locations").select("*") \
                .eq("tourist_id", tourist_id) \
                .gte("timestamp", twenty_four_hours_ago) \
                .order("timestamp", desc=True) \
                .execute()
            
            recent_locations = recent_locations_response.data
            
            if not recent_locations:
                return 0.0
            
            safe_duration = 0.0
            
            for i, location in enumerate(recent_locations):
                zone_check = self.check_location_safety(
                    float(location.get('latitude')), 
                    float(location.get('longitude'))
                )
                
                if zone_check["in_safe_zone"]:
                    # Calculate duration at this location
                    if i < len(recent_locations) - 1:
                        # Time between this location and the next (older) one
                        current_timestamp = datetime.fromisoformat(location.get('timestamp').replace('Z', '+00:00'))
                        next_timestamp = datetime.fromisoformat(recent_locations[i + 1].get('timestamp').replace('Z', '+00:00'))
                        time_diff = next_timestamp - current_timestamp
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
                alert_data = {
                    "tourist_id": tourist_id,
                    "type": AlertType.LOW_SAFETY_SCORE.value,
                    "severity": AlertSeverity.CRITICAL.value,
                    "message": f"Critical safety score: {assessment['current_score']}",
                    "description": f"Safety assessment triggered automatic alert. Reasons: {', '.join(assessment['changes'])}",
                    "auto_generated": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "active"
                }
                
                # Insert the alert into the database using safe utility
                safe_supabase_insert(self.db, "alerts", alert_data)
                
                logger.warning(f"Automatic CRITICAL alert created for tourist {tourist_id}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in automatic assessment for tourist {tourist_id}: {e}")
            raise