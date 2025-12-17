from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import List
from app.database import get_supabase
from app.models import RestrictedZone, SafeZone
from app.schemas.zones import RestrictedZoneResponse, SafeZoneResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Zone Management"])


@router.get("/getRestrictedZones", response_model=List[RestrictedZoneResponse])
async def get_restricted_zones(
    supabase: Client = Depends(get_supabase),
    is_active: bool = True
):
    """
    Get list of all restricted zones for geofencing.
    Required endpoint: /getRestrictedZones
    """
    try:
        query = supabase.table("restricted_zones").select("*")
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.execute()
        zones = result.data
        
        logger.info(f"Retrieved {len(zones)} restricted zones")
        return zones
        
    except Exception as e:
        logger.error(f"Error retrieving restricted zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restricted zones"
        )


@router.get("/safe-zones", response_model=List[SafeZoneResponse])
async def get_safe_zones(
    supabase: Client = Depends(get_supabase),
    is_active: bool = True
):
    """
    Get list of all safe zones for tourist guidance.
    """
    try:
        query = supabase.table("safe_zones").select("*")
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        safe_zones = query.all()
        logger.info(f"Retrieved {len(safe_zones)} safe zones")
        return safe_zones
        
    except Exception as e:
        logger.error(f"Error retrieving safe zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve safe zones"
        )