from fastapi import APIRouter, Depends, HTTPException, statusfrom fastapi import APIRouter, Depends, HTTPException, status

from typing import Dict, Anyfrom sqlalchemy.orm import Session

from datetime import datetimefrom typing import Dict, Any

from app.database import get_supabasefrom datetime import datetime

from app.services.supabase_adapter import SupabaseAdapterfrom app.database import get_db

from pydantic import BaseModelfrom app.models import Alert, Tourist

import loggingfrom pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["E-FIR Management"])logger = logging.getLogger(__name__)

router = APIRouter(tags=["E-FIR Management"])



class EFIRCreate(BaseModel):

    alert_id: intclass EFIRCreate(BaseModel):

    incident_description: str    alert_id: int

    incident_location: str    incident_description: str

    witnesses: str = ""    incident_location: str

    evidence: str = ""    witnesses: str = ""

    police_station: str = ""    evidence: str = ""

    officer_name: str = ""    police_station: str = ""

    officer_name: str = ""



class EFIRResponse(BaseModel):

    id: strclass EFIRResponse(BaseModel):

    alert_id: int    id: str

    tourist_id: int    alert_id: int

    incident_description: str    tourist_id: int

    incident_location: str    incident_description: str

    witnesses: str    incident_location: str

    evidence: str    witnesses: str

    police_station: str    evidence: str

    officer_name: str    police_station: str

    status: str    officer_name: str

    filed_at: datetime    status: str

    fir_number: str    filed_at: datetime

    fir_number: str



# ✅ Required Endpoint: /fileEFIR

@router.post("/fileEFIR", response_model=EFIRResponse, status_code=status.HTTP_201_CREATED)# ✅ Required Endpoint: /fileEFIR

async def file_efir_endpoint(@router.post("/fileEFIR", response_model=EFIRResponse, status_code=status.HTTP_201_CREATED)

    efir_data: EFIRCreate,async def file_efir_endpoint(

    db = Depends(get_supabase)    efir_data: EFIRCreate,

):    db: Session = Depends(get_db)

    """):

    File an electronic First Information Report (E-FIR) for an alert.    """

    Required endpoint: /fileEFIR    File an electronic First Information Report (E-FIR) for an alert.

    """    Required endpoint: /fileEFIR

    try:    """

        adapter = SupabaseAdapter(db)    try:

                # Verify alert exists and is critical

        # Verify alert exists        alert = db.query(Alert).filter(Alert.id == efir_data.alert_id).first()

        alert = adapter.get_by_id("alerts", efir_data.alert_id)        if not alert:

        if not alert:            raise HTTPException(

            raise HTTPException(                status_code=status.HTTP_404_NOT_FOUND,

                status_code=status.HTTP_404_NOT_FOUND,                detail="Alert not found"

                detail="Alert not found"            )

            )        

                # Verify tourist exists

        # Verify tourist exists        tourist = db.query(Tourist).filter(Tourist.id == alert.tourist_id).first()

        tourist_id = alert.get("tourist_id")        if not tourist:

        tourist = adapter.get_by_id("tourists", tourist_id)            raise HTTPException(

        if not tourist:                status_code=status.HTTP_404_NOT_FOUND,

            raise HTTPException(                detail="Tourist not found"

                status_code=status.HTTP_404_NOT_FOUND,            )

                detail="Tourist not found"        

            )        # Generate FIR number (format: EFIR-YYYY-MM-DD-ALERTID)

                fir_number = f"EFIR-{datetime.now().strftime('%Y-%m-%d')}-{alert.id:06d}"

        # Generate FIR number (format: EFIR-YYYY-MM-DD-ALERTID)        

        fir_number = f"EFIR-{datetime.now().strftime('%Y-%m-%d')}-{alert['id']:06d}"        # Create E-FIR record (storing in alert metadata for simplicity)

                efir_data_dict = {

        # Create E-FIR record            "id": fir_number,

        efir_data_dict = {            "alert_id": efir_data.alert_id,

            "id": fir_number,            "tourist_id": alert.tourist_id,

            "alert_id": efir_data.alert_id,            "incident_description": efir_data.incident_description,

            "tourist_id": tourist_id,            "incident_location": efir_data.incident_location,

            "incident_description": efir_data.incident_description,            "witnesses": efir_data.witnesses,

            "incident_location": efir_data.incident_location,            "evidence": efir_data.evidence,

            "witnesses": efir_data.witnesses,            "police_station": efir_data.police_station,

            "evidence": efir_data.evidence,            "officer_name": efir_data.officer_name,

            "police_station": efir_data.police_station,            "status": "FILED",

            "officer_name": efir_data.officer_name,            "filed_at": datetime.utcnow(),

            "status": "FILED",            "fir_number": fir_number

            "filed_at": datetime.utcnow().isoformat(),        }

            "fir_number": fir_number        

        }        # Update alert with E-FIR information

                if not alert.alert_metadata:

        # Update alert with E-FIR information            alert.alert_metadata = {}

        alert_metadata = alert.get("alert_metadata", {}) or {}        alert.alert_metadata["efir"] = efir_data_dict

        alert_metadata["efir"] = efir_data_dict        alert.status = "acknowledged"  # Mark alert as acknowledged

                alert.acknowledged = True

        # Update alert status        alert.acknowledged_at = datetime.utcnow()

        adapter.update("alerts", alert['id'], {        alert.acknowledged_by = efir_data.officer_name or "Police Officer"

            "alert_metadata": alert_metadata,        

            "status": "acknowledged",        db.commit()

            "acknowledged": True,        

            "acknowledged_at": datetime.utcnow().isoformat(),        logger.info(f"E-FIR {fir_number} filed for alert {alert.id} by {efir_data.officer_name}")

            "acknowledged_by": efir_data.officer_name or "Police Officer"        

        })        return EFIRResponse(**efir_data_dict)

                

        logger.info(f"E-FIR {fir_number} filed for alert {alert['id']} by {efir_data.officer_name}")    except HTTPException:

                raise

        # Convert filed_at string back to datetime    except Exception as e:

        efir_data_dict["filed_at"] = datetime.fromisoformat(efir_data_dict["filed_at"])        logger.error(f"Error filing E-FIR: {e}")

                db.rollback()

        return EFIRResponse(**efir_data_dict)        raise HTTPException(

                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

    except HTTPException:            detail="Failed to file E-FIR"

        raise        )

    except Exception as e:

        logger.error(f"Error filing E-FIR: {e}")

        raise HTTPException(@router.get("/efir/{fir_number}", response_model=EFIRResponse)

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,async def get_efir(

            detail="Failed to file E-FIR"    fir_number: str,

        )    db: Session = Depends(get_db)

):

    """Get E-FIR details by FIR number"""

@router.get("/efir/{fir_number}", response_model=EFIRResponse)    try:

async def get_efir(        # Find alert with this FIR number in metadata

    fir_number: str,        alerts = db.query(Alert).filter(Alert.alert_metadata.op("@>")({

    db = Depends(get_supabase)            "efir": {"fir_number": fir_number}

):        })).all()

    """Get E-FIR details by FIR number"""        

    try:        if not alerts:

        # We need to search through all alerts to find the one with this FIR number            raise HTTPException(

        # This is a limitation of Supabase, as we can't easily query JSON fields like in PostgreSQL                status_code=status.HTTP_404_NOT_FOUND,

        response = db.table("alerts").select("*").execute()                detail="E-FIR not found"

        alerts = response.data            )

                

        matching_alert = None        alert = alerts[0]

        efir_data = None        efir_data = alert.alert_metadata.get("efir", {})

                

        for alert in alerts:        return EFIRResponse(**efir_data)

            alert_metadata = alert.get("alert_metadata", {})        

            if not alert_metadata:    except HTTPException:

                continue        raise

                    except Exception as e:

            if isinstance(alert_metadata, str):        logger.error(f"Error retrieving E-FIR: {e}")

                import json        raise HTTPException(

                alert_metadata = json.loads(alert_metadata)            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

                            detail="Failed to retrieve E-FIR"

            efir_info = alert_metadata.get("efir", {})        )

            if efir_info and efir_info.get("fir_number") == fir_number:

                matching_alert = alert

                efir_data = efir_info@router.get("/efirs/status/{status_filter}")

                breakasync def get_efirs_by_status(

                    status_filter: str,

        if not matching_alert or not efir_data:    skip: int = 0,

            raise HTTPException(    limit: int = 100,

                status_code=status.HTTP_404_NOT_FOUND,    db: Session = Depends(get_db)

                detail="E-FIR not found"):

            )    """Get E-FIRs by status"""

            try:

        # Convert filed_at string back to datetime if needed        # Find alerts with E-FIR data

        if isinstance(efir_data["filed_at"], str):        alerts = db.query(Alert).filter(

            efir_data["filed_at"] = datetime.fromisoformat(efir_data["filed_at"])            Alert.alert_metadata.op("?")("efir")

                ).offset(skip).limit(limit).all()

        return EFIRResponse(**efir_data)        

                efirs = []

    except HTTPException:        for alert in alerts:

        raise            efir_data = alert.alert_metadata.get("efir", {})

    except Exception as e:            if efir_data.get("status", "").lower() == status_filter.lower():

        logger.error(f"Error retrieving E-FIR: {e}")                efirs.append(efir_data)

        raise HTTPException(        

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        return {"efirs": efirs, "count": len(efirs)}

            detail="Failed to retrieve E-FIR"        

        )    except Exception as e:

        logger.error(f"Error retrieving E-FIRs by status: {e}")

        raise HTTPException(

@router.get("/efirs/status/{status_filter}")            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

async def get_efirs_by_status(            detail="Failed to retrieve E-FIRs"

    status_filter: str,        )
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_supabase)
):
    """Get E-FIRs by status"""
    try:
        # Since we can't easily query JSON fields in Supabase, we'll fetch all alerts and filter
        response = db.table("alerts").select("*").execute()
        alerts = response.data
        
        efirs = []
        
        for alert in alerts:
            alert_metadata = alert.get("alert_metadata", {})
            if not alert_metadata:
                continue
                
            if isinstance(alert_metadata, str):
                import json
                alert_metadata = json.loads(alert_metadata)
                
            efir_data = alert_metadata.get("efir", {})
            if efir_data and efir_data.get("status", "").lower() == status_filter.lower():
                # Convert filed_at string to datetime if needed
                if isinstance(efir_data["filed_at"], str):
                    efir_data["filed_at"] = datetime.fromisoformat(efir_data["filed_at"])
                efirs.append(efir_data)
        
        # Apply pagination
        start_idx = min(skip, len(efirs))
        end_idx = min(skip + limit, len(efirs))
        paginated_efirs = efirs[start_idx:end_idx]
        
        return {"efirs": paginated_efirs, "count": len(efirs), "filtered_count": len(paginated_efirs)}
        
    except Exception as e:
        logger.error(f"Error retrieving E-FIRs by status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve E-FIRs"
        )