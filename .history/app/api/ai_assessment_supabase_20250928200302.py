"""
AI Assessment API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.database import get_supabase
from app.services.ai_engine_supabase import AIEngineService, get_ai_engine as get_global_ai_engine

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Assessment"])


def get_ai_engine() -> AIEngineService:
    """Get the global AI engine instance."""
    return get_global_ai_engine()


def set_ai_engine(engine_instance: AIEngineService):
    """Set global AI engine instance (used during app startup)"""
    from app.services.ai_engine_supabase import ai_service
    global ai_service
    ai_service = engine_instance


@router.post("/initialize")
async def initialize_ai_engine():
    """Initialize the AI engine (for manual initialization)."""
    try:
        engine = get_ai_engine()
        await engine.initialize()
        
        return {
            "message": "AI Engine initialized successfully",
            "status": "active",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to initialize AI engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize AI engine: {str(e)}"
        )


@router.post("/assess/{tourist_id}")
async def assess_tourist_safety(
    tourist_id: int,
    background_tasks: BackgroundTasks
):
    """
    Trigger safety assessment for a tourist
    """
    try:
        supabase = get_supabase()
        
        # Check if tourist exists
        tourist_result = supabase.table("tourists").select("*").eq("id", tourist_id).execute()
        if not tourist_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Get latest location
        location_result = supabase.table("locations").select("*").eq("tourist_id", tourist_id).order("timestamp", desc=True).limit(1).execute()
        if not location_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No location data available for this tourist"
            )
        
        latest_location = location_result.data[0]
        
        # Run assessment in background
        engine = get_ai_engine()
        background_tasks.add_task(
            engine.process_location_update,
            tourist_id,
            latest_location["latitude"],
            latest_location["longitude"]
        )
        
        return {
            "message": "Safety assessment initiated",
            "tourist_id": tourist_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in safety assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process safety assessment"
        )


@router.get("/status/{tourist_id}")
async def get_tourist_safety_status(tourist_id: int):
    """
    Get current safety status and assessment for a tourist
    """
    try:
        engine = get_ai_engine()
        result = await engine.get_safety_assessment(tourist_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting safety status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve safety status"
        )


@router.post("/bulk-assessment")
async def run_bulk_assessment(background_tasks: BackgroundTasks):
    """
    Run assessment for all active tourists
    """
    try:
        supabase = get_supabase()
        engine = get_ai_engine()
        
        # Get active tourists
        tourist_result = supabase.table("tourists").select("*").eq("is_active", True).execute()
        active_tourists = tourist_result.data
        
        for tourist in active_tourists:
            # Get latest location
            location_result = supabase.table("locations").select("*").eq("tourist_id", tourist["id"]).order("timestamp", desc=True).limit(1).execute()
            
            if location_result.data:
                latest_location = location_result.data[0]
                # Process in background
                background_tasks.add_task(
                    engine.process_location_update,
                    tourist["id"],
                    latest_location["latitude"],
                    latest_location["longitude"]
                )
        
        return {
            "message": f"Bulk assessment initiated for {len(active_tourists)} tourists",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error in bulk assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process bulk assessment"
        )