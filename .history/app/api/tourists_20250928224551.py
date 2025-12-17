"""
Tourist Management API - Supabase Implementation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.database import get_supabase
from app.schemas.tourist import TouristCreate, TouristResponse, TouristSummary, TouristUpdate
from app.services.ai_engine import get_ai_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tourist Management"])


# ✅ Required Endpoint: /tourists/register
@router.post("/tourists/register", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def register_tourist(tourist_data: TouristCreate):
    """
    Register a new tourist in the system.
    
    Required fields:
    - name: Tourist's full name
    - contact: Contact number (unique)
    - emergency_contact: Emergency contact number
    
    Optional fields:
    - email: Email address
    - trip_info: JSON object with trip details
    - age: Tourist's age
    - nationality: Tourist's nationality (defaults to Indian)
    - passport_number: Passport number
    """
    try:
        supabase = get_supabase()
        
        # Check if tourist with same contact already exists
        result = supabase.table("tourists").select("*").eq("contact", tourist_data.contact).execute()
        if result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tourist with this contact number already exists"
            )
        
        # Convert Pydantic model to dict
        tourist_dict = tourist_data.dict(exclude_unset=True)
        
        # Add default values
        tourist_dict.update({
            "safety_score": 100,  # Default safety score
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        
        # Insert into database
        result = supabase.table("tourists").insert(tourist_dict).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register tourist"
            )
        
        new_tourist = result.data[0]
        logger.info(f"Tourist registered successfully: {new_tourist['name']} (ID: {new_tourist['id']})")
        
        return new_tourist
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while registering tourist: {str(e)}"
        )


# ✅ Required Endpoint: /tourists/{id}
@router.get("/tourists/{tourist_id}", response_model=TouristResponse)
async def get_tourist(tourist_id: int):
    """
    Get detailed information about a specific tourist by ID.
    
    Returns:
    - Tourist details including safety score and contact information
    """
    try:
        supabase = get_supabase()
        
        # Get tourist data
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
        logger.error(f"Error fetching tourist data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourist information"
        )


@router.get("/tourists", response_model=List[TouristSummary])
async def list_tourists(
    active_only: bool = True,
    safety_below: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get a list of all registered tourists with optional filtering.
    
    Parameters:
    - active_only: Filter only active tourists
    - safety_below: Filter tourists with safety score below this value
    - limit: Maximum number of results to return
    - offset: Number of results to skip
    """
    try:
        supabase = get_supabase()
        
        # Start building query
        query = supabase.table("tourists").select("*")
        
        # Apply filters
        if active_only:
            query = query.eq("is_active", True)
            
        if safety_below is not None:
            query = query.lt("safety_score", safety_below)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error listing tourists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tourists list"
        )


@router.put("/tourists/{tourist_id}", response_model=TouristResponse)
async def update_tourist(tourist_id: int, tourist_data: TouristUpdate):
    """
    Update tourist information.
    
    Only provided fields will be updated.
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
        
        # Convert Pydantic model to dict, excluding unset fields
        update_data = tourist_data.dict(exclude_unset=True)
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update tourist
        result = supabase.table("tourists").update(update_data).eq("id", tourist_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tourist information"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tourist information"
        )


@router.get("/tourists/{tourist_id}/safety", response_model=Dict[str, Any])
async def get_tourist_safety(tourist_id: int):
    """
    Get comprehensive safety assessment for a tourist.
    
    Returns:
    - Safety score
    - Safety status (SAFE, WARNING, CRITICAL)
    - Active alerts
    - Recent locations
    """
    try:
        # Use AI engine to get comprehensive safety assessment
        ai_engine = get_ai_engine()
        assessment = await ai_engine.get_safety_assessment(tourist_id)
        
        if "error" in assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=assessment["error"]
            )
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tourist safety assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve safety assessment"
        )


@router.put("/tourists/{tourist_id}/deactivate", response_model=TouristResponse)
async def deactivate_tourist(tourist_id: int):
    """
    Deactivate a tourist account.
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
        
        # Deactivate tourist
        update_data = {
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("tourists").update(update_data).eq("id", tourist_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate tourist"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate tourist"
        )


@router.put("/tourists/{tourist_id}/activate", response_model=TouristResponse)
async def activate_tourist(tourist_id: int):
    """
    Activate a previously deactivated tourist account.
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
        
        # Activate tourist
        update_data = {
            "is_active": True,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("tourists").update(update_data).eq("id", tourist_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate tourist"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating tourist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate tourist"
        )


# Legacy API endpoints (same behavior but with different routes)
@router.post("/registerTourist", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def legacy_register_tourist(tourist_data: TouristCreate):
    """Legacy endpoint for registering a tourist."""
    return await register_tourist(tourist_data)


@router.post("/api/v1/tourists", response_model=TouristResponse, status_code=status.HTTP_201_CREATED)
async def api_v1_register_tourist(tourist_data: TouristCreate):
    """API v1 endpoint for registering a tourist."""
    return await register_tourist(tourist_data)


@router.get("/api/v1/tourists/{tourist_id}", response_model=TouristResponse)
async def api_v1_get_tourist(tourist_id: int):
    """API v1 endpoint for getting tourist details."""
    return await get_tourist(tourist_id)


@router.get("/api/v1/tourists", response_model=List[TouristSummary])
async def api_v1_list_tourists(
    active_only: bool = True,
    safety_below: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """API v1 endpoint for listing tourists."""
    return await list_tourists(active_only, safety_below, limit, offset)
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