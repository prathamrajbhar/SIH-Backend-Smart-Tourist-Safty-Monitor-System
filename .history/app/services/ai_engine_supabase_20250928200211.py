"""
🤖 Simplified Hybrid AI Engine for Smart Tourist Safety System (Supabase Version)
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
from geopy.distance import geodesic

from app.database import get_supabase, SupabaseSession

logger = logging.getLogger(__name__)

class AIEngineService:
    """
    🤖 Hybrid AI Engine for Smart Tourist Safety System (Supabase Version)
    
    Simplified implementation that works with Supabase directly:
    1. Rule-based Geo-fencing (restricted zones)
    2. Basic safety scoring
    """
    
    def __init__(self):
        self.supabase = get_supabase()
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the AI engine"""
        try:
            # Test connection
            result = self.supabase.table("tourists").select("count", count="exact").execute()
            self.initialized = True
            logger.info("✅ AI Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ AI Engine initialization failed: {e}")
            return False
    
    async def process_location_update(self, tourist_id: int, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Process a new location update and run AI assessment
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get restricted zones from Supabase
            zones_result = self.supabase.table("restricted_zones").select("*").execute()
            restricted_zones = zones_result.data
            
            # Get tourist info
            tourist_result = self.supabase.table("tourists").select("*").eq("id", tourist_id).execute()
            if not tourist_result.data:
                logger.error(f"Tourist not found: {tourist_id}")
                return {"error": "Tourist not found"}
            
            tourist = tourist_result.data[0]
            current_safety_score = tourist.get("safety_score", 100)
            
            # Check if in restricted zone
            in_restricted_zone = False
            danger_level = 0
            zone_name = None
            
            for zone in restricted_zones:
                # Simple point-in-polygon check would go here
                # For now, using simplified distance-based approach
                zone_coords = zone.get("coordinates", {})
                if not zone_coords:
                    continue
                    
                # Get center point of zone (simplified)
                try:
                    if isinstance(zone_coords, dict) and "coordinates" in zone_coords:
                        # GeoJSON Polygon format
                        coords = zone_coords["coordinates"][0]  # First polygon, outer ring
                        center_lat = sum(p[1] for p in coords) / len(coords)
                        center_lon = sum(p[0] for p in coords) / len(coords)
                    else:
                        continue
                        
                    # Calculate distance
                    distance = geodesic((latitude, longitude), (center_lat, center_lon)).meters
                    buffer_zone = zone.get("buffer_zone_meters", 100)
                    
                    if distance <= buffer_zone:
                        in_restricted_zone = True
                        danger_level = zone.get("danger_level", 1)
                        zone_name = zone.get("name", "Unknown Zone")
                        break
                        
                except (KeyError, IndexError, TypeError) as e:
                    logger.warning(f"Error processing zone {zone.get('id')}: {e}")
                    continue
            
            # Adjust safety score
            new_safety_score = current_safety_score
            
            if in_restricted_zone:
                # Reduce safety score based on danger level
                reduction = min(danger_level * 10, 40)  # Max reduction 40 points
                new_safety_score = max(0, current_safety_score - reduction)
            else:
                # Small increase for staying safe
                new_safety_score = min(100, current_safety_score + 2)
            
            # Update tourist safety score in Supabase
            self.supabase.table("tourists").update({"safety_score": new_safety_score}).eq("id", tourist_id).execute()
            
            # Create assessment record
            assessment = {
                "tourist_id": tourist_id,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.utcnow().isoformat(),
                "safety_score": new_safety_score,
                "in_restricted_zone": in_restricted_zone,
                "zone_name": zone_name if in_restricted_zone else None,
                "danger_level": danger_level if in_restricted_zone else 0,
            }
            
            # Create alert if in restricted zone
            if in_restricted_zone:
                alert = {
                    "tourist_id": tourist_id,
                    "type": "geofence",
                    "severity": "HIGH" if danger_level >= 4 else "MEDIUM",
                    "message": f"Tourist entered restricted zone: {zone_name}",
                    "latitude": latitude,
                    "longitude": longitude,
                    "status": "active",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                self.supabase.table("alerts").insert(alert).execute()
                assessment["alert_created"] = True
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in AI assessment: {e}")
            return {"error": str(e)}
    
    async def get_safety_assessment(self, tourist_id: int) -> Dict[str, Any]:
        """
        Get safety assessment for a tourist
        """
        try:
            # Get tourist info
            tourist_result = self.supabase.table("tourists").select("*").eq("id", tourist_id).execute()
            if not tourist_result.data:
                return {"error": "Tourist not found"}
            
            tourist = tourist_result.data[0]
            safety_score = tourist.get("safety_score", 100)
            
            # Get recent alerts
            alerts_result = self.supabase.table("alerts").select("*").eq("tourist_id", tourist_id).eq("status", "active").order("timestamp", desc=True).limit(5).execute()
            
            # Get recent locations
            locations_result = self.supabase.table("locations").select("*").eq("tourist_id", tourist_id).order("timestamp", desc=True).limit(10).execute()
            
            return {
                "tourist_id": tourist_id,
                "name": tourist.get("name"),
                "safety_score": safety_score,
                "safety_status": "SAFE" if safety_score > 80 else "WARNING" if safety_score > 50 else "CRITICAL",
                "active_alerts": len(alerts_result.data),
                "recent_locations": len(locations_result.data),
                "assessment_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting safety assessment: {e}")
            return {"error": str(e)}


# Global instance
ai_service = None

def get_ai_engine() -> AIEngineService:
    """Get the global AI engine instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIEngineService()
    return ai_service