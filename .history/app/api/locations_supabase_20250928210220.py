"""
Location Management API - Supabase Implementation
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.database import get_supabase
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse, LocationSummary
from app.services.ai_engine_supabase import get_ai_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Location Management"])


# ✅ Required Endpoint: /locations/update
@router.post("/locations/update", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def update_location(
    location_data: LocationUpdate,
    background_tasks: BackgroundTasks
):
    """
    Update tourist location and trigger safety assessment.
    
    Required:
    - tourist_id: ID of the tourist
    - latitude: Current latitude (-90 to 90)
    - longitude: Current longitude (-180 to 180)
    
    Optional:
    - altitude: Altitude in meters
    - accuracy: GPS accuracy in meters
    - speed: Speed in m/s
    - heading: Direction in degrees (0-360)
    - timestamp: Time of location update (defaults to now)
    """
    try:
        supabase = get_supabase()
        
        # Verify tourist exists and is active
        tourist_result = supabase.table("tourists").select("*").eq("id", location_data.tourist_id).execute()
        if not tourist_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        tourist = tourist_result.data[0]
        if not tourist.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tourist is inactive"
            )
        
        # Prepare location data
        location_dict = location_data.dict(exclude_unset=True)
        
        # Set timestamp if not provided
        if not location_dict.get("timestamp"):
            location_dict["timestamp"] = datetime.utcnow().isoformat()
        
        # Add created_at
        location_dict["created_at"] = datetime.utcnow().isoformat()
        
        # Store in database
        location_result = supabase.table("locations").insert(location_dict).execute()
        
        if not location_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store location update"
            )
        
        db_location = location_result.data[0]
        
        # Update tourist's last location timestamp
        supabase.table("tourists").update({
            "last_location_update": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", location_data.tourist_id).execute()
        
        # Trigger AI assessment in background
        ai_engine = get_ai_engine()
        background_tasks.add_task(
            ai_engine.process_location_update,
            location_data.tourist_id,
            location_data.latitude,
            location_data.longitude
        )
        
        logger.info(f"Location updated for tourist {location_data.tourist_id} at ({location_data.latitude}, {location_data.longitude})")
        
        return db_location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating location: {str(e)}"
        )


# ✅ Required Endpoint: /locations/all
@router.get("/locations/all", response_model=List[Dict[str, Any]])
async def get_all_tourist_locations(active_only: bool = True):
    """
    Get the latest location of all tourists.
    
    Parameters:
    - active_only: Only include active tourists
    
    Returns:
    - List of tourists with their latest location
    """
    try:
        supabase = get_supabase()
        
        # First, get all tourists
        query = supabase.table("tourists").select("*")
        if active_only:
            query = query.eq("is_active", True)
        
        tourists_result = query.execute()
        
        if not tourists_result.data:
            return []
        
        # For each tourist, get their latest location
        locations = []
        
        for tourist in tourists_result.data:
            location_result = supabase.table("locations") \
                .select("*") \
                .eq("tourist_id", tourist["id"]) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .execute()
            
            latest_location = None
            if location_result.data:
                latest_location = location_result.data[0]
            
            locations.append({
                "tourist_id": tourist["id"],
                "name": tourist["name"],
                "contact": tourist["contact"],
                "safety_score": tourist["safety_score"],
                "last_update": tourist.get("last_location_update"),
                "location": latest_location
            })
        
        return locations
        
    except Exception as e:
        logger.error(f"Error getting all tourist locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourist locations"
        )


@router.get("/locations/tourist/{tourist_id}", response_model=List[LocationResponse])
async def get_tourist_locations(
    tourist_id: int,
    limit: int = 20,
    hours: Optional[int] = None
):
    """
    Get location history for a specific tourist.
    
    Parameters:
    - tourist_id: ID of the tourist
    - limit: Maximum number of locations to return
    - hours: Only return locations from the last X hours
    """
    try:
        supabase = get_supabase()
        
        # Verify tourist exists
        tourist_result = supabase.table("tourists").select("*").eq("id", tourist_id).execute()
        if not tourist_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Build query
        query = supabase.table("locations").select("*").eq("tourist_id", tourist_id)
        
        # Filter by time if specified
        if hours:
            time_threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            query = query.gte("timestamp", time_threshold)
        
        # Order and limit
        query = query.order("timestamp", desc=True).limit(limit)
        
        # Execute
        location_result = query.execute()
        
        return location_result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tourist locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourist location history"
        )


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int):
    """
    Get details of a specific location entry by ID.
    """
    try:
        supabase = get_supabase()
        
        location_result = supabase.table("locations").select("*").eq("id", location_id).execute()
        
        if not location_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found"
            )
        
        return location_result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve location details"
        )


# Legacy API endpoints (same behavior but with different routes)
@router.post("/sendLocation", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def legacy_send_location(location_data: LocationUpdate, background_tasks: BackgroundTasks):
    """Legacy endpoint for updating location."""
    return await update_location(location_data, background_tasks)


@router.post("/api/v1/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def api_v1_create_location(location_data: LocationCreate, background_tasks: BackgroundTasks):
    """API v1 endpoint for creating location."""
    # Convert LocationCreate to LocationUpdate (they're compatible)
    update_data = LocationUpdate(**location_data.dict())
    return await update_location(update_data, background_tasks)


@router.get("/api/v1/locations/all", response_model=List[Dict[str, Any]])
async def api_v1_get_all_locations(active_only: bool = True):
    """API v1 endpoint for getting all tourist locations."""
    return await get_all_tourist_locations(active_only)