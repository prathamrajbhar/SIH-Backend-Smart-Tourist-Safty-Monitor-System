from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.database import get_db, get_supabase
from app.schemas.tourist import TouristCreate, TouristResponse, TouristSummary, TouristUpdate
from app.services.supabase_adapter import SupabaseAdapter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tourist Management"])


# ✅ Required Endpoint: /registerTourist
@router.post("/registerTourist", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def register_tourist_endpoint(
    tourist_data: TouristCreate,
    db = Depends(get_supabase)
):
    """
    Register a new tourist in the system.
    Required endpoint: /registerTourist
    """
    try:
        # Create adapter for Supabase
        adapter = SupabaseAdapter(db)
        
        # Check if contact already exists
        existing_tourists = adapter.filter_by("tourists", contact=tourist_data.contact)
        if existing_tourists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tourist with this contact number already exists"
            )
        
        # Create new tourist with safety score 100 (default)
        tourist_dict = tourist_data.dict()
        tourist_dict["safety_score"] = 100  # Ensure default safety score is set
        
        # Insert into Supabase
        db_tourist = adapter.create("tourists", tourist_dict)
        
        logger.info(f"New tourist registered: {db_tourist['id']} - {db_tourist['name']}")
        return db_tourist
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering tourist: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register tourist"
        )


# Legacy endpoint for backward compatibility  
@router.post("/register", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def register_tourist(
    tourist_data: TouristCreate,
    db = Depends(get_supabase)
):
    """Register a new tourist (legacy endpoint)"""
    return await register_tourist_endpoint(tourist_data, db)


@router.get("/tourists/{tourist_id}", response_model=TouristResponse)
async def get_tourist(
    tourist_id: int,
    db = Depends(get_supabase)
):
    """
    Get tourist details by ID including safety score and trip info.
    """
    try:
        adapter = SupabaseAdapter(db)
        tourist = adapter.get_by_id("tourists", tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        return tourist
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tourist {tourist_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tourist details"
        )


@router.get("/tourists", response_model=List[TouristSummary])
async def list_tourists(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db = Depends(get_supabase)
):
    """
    List all tourists with optional filtering.
    """
    try:
        adapter = SupabaseAdapter(db)
        
        if active_only:
            tourists = adapter.filter_by("tourists", is_active=True)
        else:
            tourists = adapter.get_all("tourists", limit=limit)
            
        # Manual pagination since we're already fetching all records
        start = min(skip, len(tourists))
        end = min(skip + limit, len(tourists))
        tourists = tourists[start:end]
        
        return tourists
        
    except Exception as e:
        logger.error(f"Error listing tourists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tourists list"
        )


@router.put("/tourists/{tourist_id}", response_model=TouristResponse)
async def update_tourist(
    tourist_id: int,
    tourist_update: TouristUpdate,
    db = Depends(get_supabase)
):
    """
    Update tourist information.
    """
    try:
        adapter = SupabaseAdapter(db)
        tourist = adapter.get_by_id("tourists", tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Update only provided fields
        update_data = tourist_update.dict(exclude_unset=True)
        
        # Update the record
        updated_tourist = adapter.update("tourists", tourist_id, update_data)
        
        logger.info(f"Tourist updated: {tourist_id}")
        return updated_tourist
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tourist {tourist_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tourist"
        )


@router.delete("/tourists/{tourist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_tourist(
    tourist_id: int,
    db = Depends(get_supabase)
):
    """
    Deactivate a tourist (soft delete).
    """
    try:
        adapter = SupabaseAdapter(db)
        tourist = adapter.get_by_id("tourists", tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Soft delete by setting is_active to false
        adapter.update("tourists", tourist_id, {"is_active": False})
        
        logger.info(f"Tourist deactivated: {tourist_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating tourist {tourist_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate tourist"
        )