from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any
from datetime import datetime
from app.database import get_supabase
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse, LocationSummary
from app.services.supabase_adapter import SupabaseAdapter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Location Management"])


# ✅ Required Endpoint: /sendLocation
@router.post("/sendLocation", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def send_location_endpoint(
    location_data: LocationUpdate,
    background_tasks: BackgroundTasks,
    db = Depends(get_supabase)
):
    """
    Send tourist location update and trigger AI safety assessment.
    Required endpoint: /sendLocation
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Verify tourist exists
        tourist = adapter.get_by_id("tourists", location_data.tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        if not tourist.get('is_active', True) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tourist is inactive"
            )
        
        # Create location record
        location_dict = location_data.dict()
        if location_dict.get('timestamp') is None:
            location_dict['timestamp'] = datetime.utcnow().isoformat()
            
        # Insert location into database
        db_location = adapter.create("locations", location_dict)
        
        # Update tourist's last location update
        adapter.update("tourists", location_data.tourist_id, {
            "last_location_update": datetime.utcnow().isoformat()
        })
        
        # 🤖 Trigger AI Assessment in background
        try:
            from app.api.ai_assessment import get_ai_engine
            engine = get_ai_engine()
            background_tasks.add_task(
                engine.assess_tourist_safety,
                tourist_id=location_data.tourist_id,
                location_id=db_location.id
            )
            logger.info(f"AI assessment triggered for tourist {location_data.tourist_id}")
        except Exception as e:
            logger.warning(f"Failed to trigger AI assessment: {e}")
        
        logger.info(f"Location updated for tourist {location_data.tourist_id}: ({location_data.latitude}, {location_data.longitude})")
        return db_location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )


# Legacy endpoint for backward compatibility  
@router.post("/update", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def update_location(
    location_data: LocationUpdate,
    background_tasks: BackgroundTasks,
    db = Depends(get_supabase)
):
    """Update tourist location (legacy endpoint)"""
    return await send_location_endpoint(location_data, background_tasks, db)


@router.get("/all", response_model=List[LocationSummary])
async def get_all_locations(
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_supabase)
):
    """
    Get latest location of all active tourists.
    """
    try:
        adapter = SupabaseAdapter(db)
        
        # Get all active tourists
        active_tourists = adapter.filter_by("tourists", is_active=True)
        
        result = []
        for tourist in active_tourists:
            # For each tourist, get their latest location
            locations_response = db.table("locations") \
                .select("*") \
                .eq("tourist_id", tourist["id"]) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .execute()
                
            if locations_response.data and len(locations_response.data) > 0:
                location = locations_response.data[0]
                result.append(LocationSummary(
                    tourist_id=location["tourist_id"],
                    tourist_name=tourist["name"],
                    latitude=float(location["latitude"]),
                    longitude=float(location["longitude"]),
                    timestamp=location["timestamp"],
                    safety_score=tourist["safety_score"]
                ))
        
        # Apply pagination
        start = min(skip, len(result))
        end = min(skip + limit, len(result))
        result = result[start:end]
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching all locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch locations"
        )


@router.get("/tourist/{tourist_id}", response_model=List[LocationResponse])
async def get_tourist_locations(
    tourist_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get location history for a specific tourist.
    """
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Get locations ordered by most recent
        locations = db.query(Location).filter(
            Location.tourist_id == tourist_id
        ).order_by(
            desc(Location.timestamp)
        ).limit(limit).all()
        
        return locations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching locations for tourist {tourist_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tourist locations"
        )


@router.get("/latest/{tourist_id}", response_model=LocationResponse)
async def get_latest_location(
    tourist_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the latest location for a specific tourist.
    """
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Get the latest location
        location = db.query(Location).filter(
            Location.tourist_id == tourist_id
        ).order_by(
            desc(Location.timestamp)
        ).first()
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No location data found for this tourist"
            )
        
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest location for tourist {tourist_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch latest location"
        )