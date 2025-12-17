"""
Tourist Management API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging
from datetime import datetime

from app.database import get_supabase
from app.schemas.tourist import TouristCreate, TouristResponse, TouristSummary, TouristUpdate

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tourist Management"])


# ✅ Required Endpoint: /registerTourist
@router.post("/registerTourist", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def register_tourist_endpoint(tourist_data: TouristCreate):
    """
    Register a new tourist in the system.
    Required endpoint: /registerTourist
    """
    try:
        supabase = get_supabase()
        
        # Check if contact already exists
        result = supabase.table("tourists").select("*").eq("contact", tourist_data.contact).execute()
        if result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tourist with this contact number already exists"
            )
        
        # Create new tourist with safety score 100 (default)
        tourist_dict = tourist_data.dict()
        tourist_dict["safety_score"] = 100
        tourist_dict["is_active"] = True
        tourist_dict["created_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("tourists").insert(tourist_dict).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register tourist in database"
            )
        
        db_tourist = result.data[0]
        logger.info(f"New tourist registered: {db_tourist['id']} - {db_tourist['name']}")
        
        return db_tourist
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register tourist"
        )


@router.post("/api/v1/tourists", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def create_tourist(tourist_data: TouristCreate):
    """
    Create a new tourist (API v1 endpoint).
    """
    return await register_tourist_endpoint(tourist_data)


@router.get("/tourists/{tourist_id}", response_model=TouristResponse)
@router.get("/api/v1/tourists/{tourist_id}", response_model=TouristResponse)
async def get_tourist(tourist_id: int):
    """
    Get tourist details by ID.
    """
    try:
        supabase = get_supabase()
        result = supabase.table("tourists").select("*").eq("id", tourist_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourist information"
        )


@router.get("/tourists", response_model=List[TouristSummary])
@router.get("/api/v1/tourists", response_model=List[TouristSummary])
async def list_tourists(active_only: bool = True, skip: int = 0, limit: int = 100):
    """
    List all tourists, with optional filtering.
    """
    try:
        supabase = get_supabase()
        query = supabase.table("tourists").select("*")
        
        if active_only:
            query = query.eq("is_active", True)
        
        # Supabase ranges are inclusive, so we need to adjust
        result = query.range(skip, skip + limit - 1).execute()
        return result.data
        
    except Exception as e:
        logger.error(f"Error listing tourists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourists"
        )


@router.put("/tourists/{tourist_id}", response_model=TouristResponse)
@router.put("/api/v1/tourists/{tourist_id}", response_model=TouristResponse)
async def update_tourist(tourist_id: int, tourist_data: TouristUpdate):
    """
    Update tourist details.
    """
    try:
        supabase = get_supabase()
        
        # Check if tourist exists
        check_result = supabase.table("tourists").select("*").eq("id", tourist_id).execute()
        if not check_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Update tourist
        update_data = tourist_data.dict(exclude_unset=True)
        result = supabase.table("tourists").update(update_data).eq("id", tourist_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tourist"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tourist"
        )