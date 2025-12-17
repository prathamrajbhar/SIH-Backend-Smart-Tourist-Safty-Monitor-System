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
    db: Session = Depends(get_db),
    is_active: bool = True
):
    """
    Get list of all restricted zones for geofencing.
    Required endpoint: /getRestrictedZones
    """
    try:
        query = db.query(RestrictedZone)
        if is_active is not None:
            query = query.filter(RestrictedZone.is_active == is_active)
        
        restricted_zones = query.all()
        logger.info(f"Retrieved {len(restricted_zones)} restricted zones")
        return restricted_zones
        
    except Exception as e:
        logger.error(f"Error retrieving restricted zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restricted zones"
        )


@router.get("/safe-zones", response_model=List[SafeZoneResponse])
async def get_safe_zones(
    db: Session = Depends(get_db),
    is_active: bool = True
):
    """
    Get list of all safe zones for tourist guidance.
    """
    try:
        query = db.query(SafeZone)
        if is_active is not None:
            query = query.filter(SafeZone.is_active == is_active)
        
        safe_zones = query.all()
        logger.info(f"Retrieved {len(safe_zones)} safe zones")
        return safe_zones
        
    except Exception as e:
        logger.error(f"Error retrieving safe zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve safe zones"
        )