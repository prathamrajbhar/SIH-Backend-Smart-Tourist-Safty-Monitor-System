"""
Restricted Zones Management API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import logging
import json
from datetime import datetime

from app.database import get_supabase
from app.schemas.alert import GeofenceAlertCreate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Restricted Zones"])

# Helper function to check if a point is inside a polygon using ray-casting algorithm
def is_point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon using ray-casting algorithm
    
    Args:
        point: tuple (latitude, longitude)
        polygon: list of tuples [(lat1, lon1), (lat2, lon2), ...]
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


# ✅ Required Endpoint: /getRestrictedZones
@router.get("/getRestrictedZones", response_model=List[Dict[str, Any]])
async def get_restricted_zones_endpoint():
    """
    Get all restricted zones.
    Required endpoint: /getRestrictedZones
    """
    try:
        supabase = get_supabase()
        result = supabase.table("restricted_zones").select("*").execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error getting restricted zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restricted zones"
        )


@router.post("/api/v1/zones/restricted", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_restricted_zone(
    name: str,
    coordinates: List[List[float]],
    danger_level: int,
    description: Optional[str] = None,
    buffer_zone_meters: Optional[int] = 100
):
    """
    Create a new restricted zone
    """
    try:
        supabase = get_supabase()
        
        # Validate inputs
        if danger_level < 1 or danger_level > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Danger level must be between 1 and 5"
            )
        
        if len(coordinates) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Polygon must have at least 3 points"
            )
        
        # Create GeoJSON polygon format
        geojson_polygon = {
            "type": "Polygon",
            "coordinates": [coordinates]
        }
        
        # Create restricted zone data
        zone_data = {
            "name": name,
            "description": description or f"Restricted zone with danger level {danger_level}",
            "coordinates": json.dumps(geojson_polygon),
            "danger_level": danger_level,
            "buffer_zone_meters": buffer_zone_meters,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert restricted zone
        result = supabase.table("restricted_zones").insert(zone_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create restricted zone"
            )
            
        logger.info(f"Created restricted zone: {name} with danger level {danger_level}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating restricted zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create restricted zone"
        )


@router.get("/api/v1/zones/restricted/{zone_id}", response_model=Dict[str, Any])
async def get_restricted_zone(zone_id: int):
    """
    Get a specific restricted zone by ID
    """
    try:
        supabase = get_supabase()
        result = supabase.table("restricted_zones").select("*").eq("id", zone_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restricted zone not found"
            )
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting restricted zone {zone_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restricted zone"
        )


# ✅ Utility Endpoint: /checkLocationInZone
@router.post("/checkLocationInZone", response_model=Dict[str, Any])
async def check_location_in_zone(
    tourist_id: int,
    latitude: float,
    longitude: float
):
    """
    Check if a location is within any restricted zone.
    Utility endpoint: /checkLocationInZone
    """
    try:
        supabase = get_supabase()
        
        # Get all restricted zones
        zones_result = supabase.table("restricted_zones").select("*").execute()
        zones = zones_result.data
        
        inside_zones = []
        point = (latitude, longitude)
        
        for zone in zones:
            coordinates_json = json.loads(zone["coordinates"])
            polygon_coords = coordinates_json["coordinates"][0]
            
            # Convert to (lat, lon) format for checking
            polygon = [(coord[1], coord[0]) for coord in polygon_coords]
            
            if is_point_in_polygon(point, polygon):
                inside_zones.append({
                    "zone_id": zone["id"],
                    "name": zone["name"],
                    "danger_level": zone["danger_level"],
                    "description": zone["description"]
                })
                
                # Create geofence alert
                alert_data = GeofenceAlertCreate(
                    tourist_id=tourist_id,
                    type="geofence",
                    severity="HIGH" if zone["danger_level"] >= 4 else "MEDIUM",
                    message=f"Entered restricted zone: {zone['name']}",
                    latitude=latitude,
                    longitude=longitude,
                    auto_generated=True
                )
                
                # Insert the alert using direct Supabase call
                alert = {
                    "tourist_id": tourist_id,
                    "type": "geofence",
                    "severity": "HIGH" if zone["danger_level"] >= 4 else "MEDIUM",
                    "message": f"Entered restricted zone: {zone['name']}",
                    "latitude": latitude,
                    "longitude": longitude,
                    "auto_generated": True,
                    "status": "active",
                    "timestamp": datetime.utcnow().isoformat()
                }
                supabase.table("alerts").insert(alert).execute()
                
                # Update tourist safety score
                tourist_result = supabase.table("tourists").select("*").eq("id", tourist_id).execute()
                
                if tourist_result.data:
                    tourist = tourist_result.data[0]
                    current_score = tourist.get("safety_score", 100)
                    
                    # Reduce score based on danger level
                    reduction = zone["danger_level"] * 5  # Scale penalty by danger level
                    new_score = max(0, current_score - reduction)
                    
                    supabase.table("tourists").update({
                        "safety_score": new_score
                    }).eq("id", tourist_id).execute()
        
        return {
            "in_restricted_zone": len(inside_zones) > 0,
            "zones": inside_zones,
            "count": len(inside_zones)
        }
        
    except Exception as e:
        logger.error(f"Error checking location in zone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check location"
        )