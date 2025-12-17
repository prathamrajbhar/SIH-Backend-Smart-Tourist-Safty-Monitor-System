"""
Location Management API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any
import logging
from datetime import datetime

from app.database import get_supabase
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse, LocationSummary
from app.services.ai_engine_supabase import get_ai_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Location Management"])


# ✅ Required Endpoint: /sendLocation
@router.post("/sendLocation", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def send_location_endpoint(
    location_data: LocationUpdate,
    background_tasks: BackgroundTasks
):
    """
    Send tourist location update and trigger AI safety assessment.
    Required endpoint: /sendLocation
    """
    try:
        supabase = get_supabase()
        
        # Verify tourist exists
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
        
        # Create location record
        location_dict = location_data.dict()
        if location_dict.get('timestamp') is None:
            location_dict['timestamp'] = datetime.utcnow().isoformat()
            
        # Insert into Supabase
        location_result = supabase.table("locations").insert(location_dict).execute()
        
        if not location_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record location"
            )
        
        db_location = location_result.data[0]
        
        # Update tourist's last location update
        supabase.table("tourists").update({
            "last_location_update": datetime.utcnow().isoformat()
        }).eq("id", location_data.tourist_id).execute()
        
        # Trigger AI assessment in background
        ai_engine = get_ai_engine()
        background_tasks.add_task(
            ai_engine.process_location_update,
            location_data.tourist_id,
            location_data.latitude,
            location_data.longitude
        )
        
        logger.info(f"Location recorded for tourist {location_data.tourist_id} at ({location_data.latitude}, {location_data.longitude})")
        return db_location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record location"
        )


@router.post("/api/v1/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    background_tasks: BackgroundTasks
):
    """
    Create a new location record (API v1 endpoint).
    """
    return await send_location_endpoint(location_data, background_tasks)


@router.get("/api/v1/locations/all", response_model=List[LocationSummary])
async def get_all_tourist_locations():
    """
    Get latest location of all tourists
    """
    try:
        supabase = get_supabase()
        
        # This is a more complex query, so we'll use a raw SQL query via Supabase
        # Equivalent to getting the most recent location for each tourist
        # In a real implementation, this would be optimized
        
        # For now, we'll just get all locations and filter in Python
        locations_result = supabase.table("locations").select("*").execute()
        all_locations = locations_result.data
        
        # Group by tourist_id and find latest for each
        tourist_locations = {}
        for loc in all_locations:
            tourist_id = loc.get("tourist_id")
            timestamp = loc.get("timestamp")
            
            if not tourist_id or not timestamp:
                continue
                
            if tourist_id not in tourist_locations or timestamp > tourist_locations[tourist_id].get("timestamp"):
                tourist_locations[tourist_id] = loc
        
        # Convert to list
        latest_locations = list(tourist_locations.values())
        
        return latest_locations
        
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve locations"
        )


@router.get("/api/v1/locations/{tourist_id}", response_model=List[LocationSummary])
async def get_tourist_locations(
    tourist_id: int, 
    limit: int = 10
):
    """
    Get location history for a tourist
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
        
        # Get locations
        locations_result = supabase.table("locations").select("*").eq("tourist_id", tourist_id).order("timestamp", desc=True).limit(limit).execute()
        
        return locations_result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tourist locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourist locations"
        )