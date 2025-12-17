from fastapi import APIRouter, Depends, HTTPException, statusfrom fastapi import APIRouter, Depends, HTTPException, statusfrom fastapi import APIRouter, Depends, HTTPException, status

from typing import Dict, Any

from datetime import datetimefrom typing import Dict, Anyfrom sqlalchemy.orm import Session

from app.database import get_supabase

from app.services.supabase_adapter import SupabaseAdapterfrom datetime import datetimefrom typing import Dict, Any

from pydantic import BaseModel

import loggingfrom app.database import get_supabasefrom datetime import datetime

import uuid

from app.services.supabase_adapter import SupabaseAdapterfrom app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["E-FIR Management"])from pydantic import BaseModelfrom app.models import Alert, Tourist



import loggingfrom pydantic import BaseModel

class EFIRCreate(BaseModel):

    tourist_id: intimport logging

    incident_type: str

    description: strlogger = logging.getLogger(__name__)

    location: str

    incident_datetime: strrouter = APIRouter(tags=["E-FIR Management"])logger = logging.getLogger(__name__)

    additional_info: Dict[str, Any] = {}

router = APIRouter(tags=["E-FIR Management"])



class EFIRResponse(BaseModel):

    id: str

    tourist_id: intclass EFIRCreate(BaseModel):

    incident_type: str

    description: str    alert_id: intclass EFIRCreate(BaseModel):

    location: str

    incident_datetime: str    incident_description: str    alert_id: int

    additional_info: Dict[str, Any]

    status: str    incident_location: str    incident_description: str

    filed_at: str

    fir_number: str    witnesses: str = ""    incident_location: str

    police_station: str

    officer_name: str = ""    evidence: str = ""    witnesses: str = ""



    police_station: str = ""    evidence: str = ""

# ✅ Required Endpoint: /fileEFIR

@router.post("/fileEFIR", response_model=EFIRResponse, status_code=status.HTTP_201_CREATED)    officer_name: str = ""    police_station: str = ""

async def file_efir_endpoint(

    efir_data: EFIRCreate,    officer_name: str = ""

    db = Depends(get_supabase)

):

    """

    File an electronic First Information Report (E-FIR).class EFIRResponse(BaseModel):

    Required endpoint: /fileEFIR

    """    id: strclass EFIRResponse(BaseModel):

    try:

        adapter = SupabaseAdapter(db)    alert_id: int    id: str

        

        # Verify tourist exists    tourist_id: int    alert_id: int

        tourist = adapter.get_by_id("tourists", efir_data.tourist_id)

        if not tourist:    incident_description: str    tourist_id: int

            raise HTTPException(

                status_code=status.HTTP_404_NOT_FOUND,    incident_location: str    incident_description: str

                detail="Tourist not found"

            )    witnesses: str    incident_location: str

            

        # Generate unique FIR number    evidence: str    witnesses: str

        fir_number = f"FIR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

            police_station: str    evidence: str

        # Create E-FIR record

        efir_dict = efir_data.dict()    officer_name: str    police_station: str

        

        # Add additional fields    status: str    officer_name: str

        efir_dict.update({

            "status": "filed",    filed_at: datetime    status: str

            "filed_at": datetime.utcnow().isoformat(),

            "fir_number": fir_number,    fir_number: str    filed_at: datetime

            "police_station": "Nearest Police Station",  # In real app, determine based on location

        })    fir_number: str

        

        # Insert into database

        table = db.table("efirs")

        response = table.insert(efir_dict).execute()# ✅ Required Endpoint: /fileEFIR

        

        if not response.data or len(response.data) == 0:@router.post("/fileEFIR", response_model=EFIRResponse, status_code=status.HTTP_201_CREATED)# ✅ Required Endpoint: /fileEFIR

            raise Exception("Failed to insert E-FIR record")

            async def file_efir_endpoint(@router.post("/fileEFIR", response_model=EFIRResponse, status_code=status.HTTP_201_CREATED)

        efir = response.data[0]

            efir_data: EFIRCreate,async def file_efir_endpoint(

        # Create alert for this E-FIR

        alert_data = {    db = Depends(get_supabase)    efir_data: EFIRCreate,

            "tourist_id": efir_data.tourist_id,

            "type": "manual",  # This is a manually filed report):    db: Session = Depends(get_db)

            "severity": "HIGH",

            "message": f"E-FIR Filed: {efir_data.incident_type}",    """):

            "description": efir_data.description[:200] + "..." if len(efir_data.description) > 200 else efir_data.description,

            "status": "active",    File an electronic First Information Report (E-FIR) for an alert.    """

            "timestamp": datetime.utcnow().isoformat()

        }    Required endpoint: /fileEFIR    File an electronic First Information Report (E-FIR) for an alert.

        

        adapter.create("alerts", alert_data)    """    Required endpoint: /fileEFIR

        

        logger.info(f"E-FIR filed with number {fir_number} for tourist {efir_data.tourist_id}")    try:    """

        return efir

                adapter = SupabaseAdapter(db)    try:

    except HTTPException:

        raise                # Verify alert exists and is critical

    except Exception as e:

        logger.error(f"Error filing E-FIR: {e}")        # Verify alert exists        alert = db.query(Alert).filter(Alert.id == efir_data.alert_id).first()

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        alert = adapter.get_by_id("alerts", efir_data.alert_id)        if not alert:

            detail="Failed to file E-FIR"

        )        if not alert:            raise HTTPException(

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