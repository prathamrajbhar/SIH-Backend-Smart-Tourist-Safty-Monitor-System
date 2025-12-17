"""
eFIR (Electronic First Information Report) API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from typing import List, Optional
import logging
from datetime import datetime
import os
import uuid
import json

from app.database import get_supabase
from app.schemas.alert import AlertResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["eFIR Management"])

# Helper functions for eFIR processing
def generate_fir_number():
    """Generate a unique FIR number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8]
    return f"FIR-{timestamp}-{random_suffix}"


# ✅ Required Endpoint: /reportIncident
@router.post("/reportIncident", response_model=dict, status_code=status.HTTP_201_CREATED)
async def report_incident_endpoint(
    tourist_id: int,
    incident_type: str,
    description: str,
    latitude: float,
    longitude: float,
    occurred_at: Optional[datetime] = None,
    evidence_files: List[UploadFile] = File([])
):
    """
    Report a tourism-related incident and generate an eFIR.
    Required endpoint: /reportIncident
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
            
        tourist = tourist_result.data[0]
        
        # Generate FIR number and prepare eFIR data
        fir_number = generate_fir_number()
        
        # Use current time if occurred_at not provided
        if occurred_at is None:
            occurred_at = datetime.utcnow()
            
        # Prepare eFIR record
        efir_data = {
            "fir_number": fir_number,
            "tourist_id": tourist_id,
            "tourist_name": tourist.get("name", "Unknown"),
            "incident_type": incident_type,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "occurred_at": occurred_at.isoformat(),
            "reported_at": datetime.utcnow().isoformat(),
            "status": "submitted",
            "evidence_count": len(evidence_files),
            "has_evidence": len(evidence_files) > 0
        }
        
        # Insert eFIR record
        result = supabase.table("efirs").insert(efir_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create eFIR"
            )
            
        efir_id = result.data[0]["id"]
        
        # Process and upload any evidence files to Supabase storage
        evidence_paths = []
        
        for i, file in enumerate(evidence_files):
            content = await file.read()
            file_ext = os.path.splitext(file.filename)[1]
            storage_path = f"efir_evidence/{fir_number}/{i+1}{file_ext}"
            
            # Upload to Supabase Storage
            storage_result = supabase.storage.from_("efir-evidence").upload(
                storage_path,
                content
            )
            
            # Record evidence path
            evidence_paths.append(storage_path)
        
        # If we have evidence files, update the eFIR record with paths
        if evidence_paths:
            supabase.table("efirs").update({
                "evidence_paths": json.dumps(evidence_paths)
            }).eq("id", efir_id).execute()
            
        # Create a corresponding alert
        alert_data = {
            "tourist_id": tourist_id,
            "type": "efir",
            "severity": "MEDIUM",  # Default severity for eFIRs
            "message": f"eFIR {fir_number}: {incident_type} incident reported",
            "latitude": latitude,
            "longitude": longitude,
            "auto_generated": True,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Insert alert
        supabase.table("alerts").insert(alert_data).execute()
        
        logger.info(f"eFIR {fir_number} created for tourist {tourist_id}")
        
        # Return eFIR details
        return {
            "fir_number": fir_number,
            "id": efir_id,
            "status": "submitted",
            "message": "Incident report submitted successfully",
            "evidence_count": len(evidence_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating eFIR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create eFIR: {str(e)}"
        )


@router.get("/api/v1/efirs", response_model=List[dict])
async def get_efirs(tourist_id: Optional[int] = None):
    """
    Get all eFIRs, optionally filtered by tourist
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("efirs").select("*")
        
        if tourist_id is not None:
            query = query.eq("tourist_id", tourist_id)
            
        # Order by reported_at descending (most recent first)
        result = query.order("reported_at", desc=True).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error retrieving eFIRs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve eFIRs"
        )


@router.get("/api/v1/efirs/{fir_number}", response_model=dict)
async def get_efir_by_number(fir_number: str):
    """
    Get eFIR details by FIR number
    """
    try:
        supabase = get_supabase()
        
        result = supabase.table("efirs").select("*").eq("fir_number", fir_number).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eFIR not found"
            )
            
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving eFIR {fir_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve eFIR"
        )