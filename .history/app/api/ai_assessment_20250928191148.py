from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.database import get_supabase
from app.services.supabase_adapter import SupabaseAdapter
from app.services.ai_engine import AIEngineService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Assessment"])

ai_engine: Optional[AIEngineService] = None

# Global AI engine instance (will be initialized on startup)

ai_engine: Optional[AIEngineService] = None

def get_ai_engine() -> AIEngineService:

    """Get the global AI engine instance."""

    global ai_enginedef get_ai_engine() -> AIEngineService:

    if ai_engine is None:    """Get the global AI engine instance."""

        raise HTTPException(    global ai_engine

            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,    if ai_engine is None:

            detail="AI Engine not initialized"        raise HTTPException(

        )            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,

    return ai_engine            detail="AI Engine not initialized"

        )

    return ai_engine

@router.post("/initialize")

async def initialize_ai_engine(db = Depends(get_supabase)):

    """Initialize the AI engine (for manual initialization)."""@router.post("/initialize")

    global ai_engineasync def initialize_ai_engine():

    try:    """Initialize the AI engine (for manual initialization)."""

        if ai_engine is None:    global ai_engine

            ai_engine = AIEngineService(db)    try:

            await ai_engine.initialize()        if ai_engine is None:

                    ai_engine = AIEngineService()

        return {            await ai_engine.initialize()

            "message": "AI Engine initialized successfully",        

            "status": "active",        return {

            "timestamp": datetime.utcnow()            "message": "AI Engine initialized successfully",

        }            "status": "active",

    except Exception as e:            "timestamp": datetime.utcnow()

        logger.error(f"Failed to initialize AI engine: {e}")        }

        raise HTTPException(    except Exception as e:

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        logger.error(f"Failed to initialize AI engine: {e}")

            detail=f"Failed to initialize AI engine: {str(e)}"        raise HTTPException(

        )            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=f"Failed to initialize AI engine: {str(e)}"

        )

@router.get("/status")

async def get_ai_status():

    """Get AI engine status and model information."""@router.get("/status")

    try:async def get_ai_status():

        engine = get_ai_engine()    """Get AI engine status and model information."""

        status_info = engine.get_model_status()    try:

                engine = get_ai_engine()

        return {        status_info = engine.get_model_status()

            "status": "active",        

            "timestamp": datetime.utcnow(),        return {

            **status_info            "status": "active",

        }            "timestamp": datetime.utcnow(),

    except HTTPException:            **status_info

        raise        }

    except Exception as e:    except HTTPException:

        logger.error(f"Error getting AI status: {e}")        raise

        raise HTTPException(    except Exception as e:

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        logger.error(f"Error getting AI status: {e}")

            detail="Failed to get AI status"        raise HTTPException(

        )            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail="Failed to get AI status"

        )

@router.post("/assess/{tourist_id}")

async def create_immediate_assessment(

    tourist_id: int,@router.post("/assess/{tourist_id}")

    background_tasks: BackgroundTasks,async def create_immediate_assessment(

    db = Depends(get_supabase)    tourist_id: int,

):    background_tasks: BackgroundTasks,

    """Create an immediate AI assessment for a specific tourist."""    db: Session = Depends(get_db)

    try:):

        adapter = SupabaseAdapter(db)    """Create an immediate AI assessment for a specific tourist."""

            try:

        # Verify tourist exists        # Verify tourist exists

        tourist = adapter.get_by_id("tourists", tourist_id)        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()

        if not tourist:        if not tourist:

            raise HTTPException(            raise HTTPException(

                status_code=status.HTTP_404_NOT_FOUND,                status_code=status.HTTP_404_NOT_FOUND,

                detail="Tourist not found"                detail="Tourist not found"

            )            )

                

        # Get latest location        # Get latest location

        locations = adapter.filter_by("locations", tourist_id=tourist_id)        latest_location = db.query(Location).filter(

        if not locations:            Location.tourist_id == tourist_id

            raise HTTPException(        ).order_by(Location.timestamp.desc()).first()

                status_code=status.HTTP_404_NOT_FOUND,        

                detail="No location data found for tourist"        if not latest_location:

            )            raise HTTPException(

                        status_code=status.HTTP_404_NOT_FOUND,

        # Sort by timestamp descending                detail="No location data found for tourist"

        latest_location = sorted(            )

            locations,         

            key=lambda x: x.get("timestamp", ""),         # Get AI engine and create assessment

            reverse=True        engine = get_ai_engine()

        )[0]        

                # Run assessment in background

        # Get AI engine and create assessment        background_tasks.add_task(

        engine = get_ai_engine()            engine.create_ai_assessment,

                    latest_location

        # Run assessment in background        )

        background_tasks.add_task(        

            engine.create_ai_assessment,        return {

            latest_location            "message": "AI assessment initiated",

        )            "tourist_id": tourist_id,

                    "location_id": latest_location.id,

        return {            "timestamp": datetime.utcnow()

            "message": "AI assessment initiated",        }

            "tourist_id": tourist_id,        

            "location_id": latest_location.get("id"),    except HTTPException:

            "timestamp": datetime.utcnow()        raise

        }    except Exception as e:

                logger.error(f"Error creating immediate assessment for tourist {tourist_id}: {e}")

    except HTTPException:        raise HTTPException(

        raise            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

    except Exception as e:            detail="Failed to create AI assessment"

        logger.error(f"Error creating immediate assessment for tourist {tourist_id}: {e}")        )

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail="Failed to create AI assessment"@router.get("/assessment/{tourist_id}")

        )async def get_tourist_assessments(

    tourist_id: int,

    limit: int = 10,

@router.get("/assessment/{tourist_id}")    db: Session = Depends(get_db)

async def get_tourist_assessments():

    tourist_id: int,    """Get recent AI assessments for a specific tourist."""

    limit: int = 10,    try:

    db = Depends(get_supabase)        # Verify tourist exists

):        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()

    """Get recent AI assessments for a specific tourist."""        if not tourist:

    try:            raise HTTPException(

        adapter = SupabaseAdapter(db)                status_code=status.HTTP_404_NOT_FOUND,

                        detail="Tourist not found"

        # Verify tourist exists            )

        tourist = adapter.get_by_id("tourists", tourist_id)        

        if not tourist:        # Get assessments

            raise HTTPException(        assessments = db.query(AIAssessment).filter(

                status_code=status.HTTP_404_NOT_FOUND,            AIAssessment.tourist_id == tourist_id

                detail="Tourist not found"        ).order_by(

            )            AIAssessment.created_at.desc()

                ).limit(limit).all()

        # Get assessments        

        response = db.table("ai_assessments") \        # Format response

            .select("*") \        result = []

            .eq("tourist_id", tourist_id) \        for assessment in assessments:

            .order("created_at", desc=True) \            result.append({

            .limit(limit) \                "id": assessment.id,

            .execute()                "safety_score": assessment.safety_score,

                            "severity": assessment.severity.value,

        assessments = response.data                "geofence_alert": assessment.geofence_alert,

                        "anomaly_score": float(assessment.anomaly_score) if assessment.anomaly_score else None,

        # Format response                "temporal_risk_score": float(assessment.temporal_risk_score) if assessment.temporal_risk_score else None,

        result = []                "confidence_level": float(assessment.confidence_level),

        for assessment in assessments:                "recommended_action": assessment.recommended_action,

            result.append({                "alert_message": assessment.alert_message,

                "id": assessment.get("id"),                "model_versions": assessment.model_versions,

                "safety_score": assessment.get("safety_score"),                "created_at": assessment.created_at

                "severity": assessment.get("severity"),            })

                "geofence_alert": assessment.get("geofence_alert", False),        

                "anomaly_score": float(assessment.get("anomaly_score", 0)) if assessment.get("anomaly_score") else None,        return {

                "temporal_risk_score": float(assessment.get("temporal_risk_score", 0)) if assessment.get("temporal_risk_score") else None,            "tourist_id": tourist_id,

                "confidence_level": float(assessment.get("confidence_level", 0)),            "assessments": result,

                "recommended_action": assessment.get("recommended_action"),            "total_count": len(result)

                "alert_message": assessment.get("alert_message"),        }

                "model_versions": assessment.get("model_versions", {}),        

                "created_at": assessment.get("created_at")    except HTTPException:

            })        raise

            except Exception as e:

        return {        logger.error(f"Error getting assessments for tourist {tourist_id}: {e}")

            "tourist_id": tourist_id,        raise HTTPException(

            "assessments": result,            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            "total_count": len(result)            detail="Failed to get AI assessments"

        }        )

        

    except HTTPException:

        raise@router.get("/predictions/{assessment_id}")

    except Exception as e:async def get_model_predictions(

        logger.error(f"Error getting assessments for tourist {tourist_id}: {e}")    assessment_id: int,

        raise HTTPException(    db: Session = Depends(get_db)

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,):

            detail="Failed to get AI assessments"    """Get detailed model predictions for a specific assessment."""

        )    try:

        # Get assessment

        assessment = db.query(AIAssessment).filter(AIAssessment.id == assessment_id).first()

@router.get("/predictions/{assessment_id}")        if not assessment:

async def get_model_predictions(            raise HTTPException(

    assessment_id: int,                status_code=status.HTTP_404_NOT_FOUND,

    db = Depends(get_supabase)                detail="Assessment not found"

):            )

    """Get detailed model predictions for a specific assessment."""        

    try:        # Get predictions

        adapter = SupabaseAdapter(db)        predictions = db.query(AIModelPrediction).filter(

                    AIModelPrediction.assessment_id == assessment_id

        # Get assessment        ).all()

        assessment = adapter.get_by_id("ai_assessments", assessment_id)        

        if not assessment:        # Format response

            raise HTTPException(        prediction_details = []

                status_code=status.HTTP_404_NOT_FOUND,        for pred in predictions:

                detail="Assessment not found"            prediction_details.append({

            )                "id": pred.id,

                        "model_name": pred.model_name.value,

        # Get predictions                "prediction_value": float(pred.prediction_value),

        response = db.table("ai_model_predictions") \                "confidence": float(pred.confidence),

            .select("*") \                "processing_time_ms": float(pred.processing_time_ms) if pred.processing_time_ms else None,

            .eq("assessment_id", assessment_id) \                "model_version": pred.model_version,

            .execute()                "metadata": pred.metadata,

                            "created_at": pred.created_at

        predictions = response.data            })

                

        # Format response        return {

        prediction_details = []            "assessment_id": assessment_id,

        for pred in predictions:            "tourist_id": assessment.tourist_id,

            prediction_details.append({            "overall_assessment": {

                "id": pred.get("id"),                "safety_score": assessment.safety_score,

                "model_name": pred.get("model_name"),                "severity": assessment.severity.value,

                "prediction_value": float(pred.get("prediction_value", 0)),                "confidence_level": float(assessment.confidence_level),

                "confidence": float(pred.get("confidence", 0)),                "recommended_action": assessment.recommended_action

                "processing_time_ms": float(pred.get("processing_time_ms", 0)) if pred.get("processing_time_ms") else None,            },

                "model_version": pred.get("model_version"),            "model_predictions": prediction_details

                "metadata": pred.get("metadata", {}),        }

                "created_at": pred.get("created_at")        

            })    except HTTPException:

                raise

        return {    except Exception as e:

            "assessment_id": assessment_id,        logger.error(f"Error getting predictions for assessment {assessment_id}: {e}")

            "tourist_id": assessment.get("tourist_id"),        raise HTTPException(

            "overall_assessment": {            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

                "safety_score": assessment.get("safety_score"),            detail="Failed to get model predictions"

                "severity": assessment.get("severity"),        )

                "confidence_level": float(assessment.get("confidence_level", 0)),

                "recommended_action": assessment.get("recommended_action")

            },@router.post("/retrain/{model_type}")

            "model_predictions": prediction_detailsasync def trigger_model_retraining(

        }    model_type: str,

            background_tasks: BackgroundTasks

    except HTTPException:):

        raise    """Trigger manual retraining of a specific model type."""

    except Exception as e:    try:

        logger.error(f"Error getting predictions for assessment {assessment_id}: {e}")        if model_type not in ['isolation_forest', 'temporal_autoencoder', 'all', 'force_all']:

        raise HTTPException(            raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,                status_code=status.HTTP_400_BAD_REQUEST,

            detail="Failed to get model predictions"                detail="Invalid model type. Must be 'isolation_forest', 'temporal_autoencoder', 'all', or 'force_all'"

        )            )

        

        engine = get_ai_engine()

@router.post("/retrain/{model_type}")        

async def trigger_model_retraining(        # Trigger retraining in background

    model_type: str,        if model_type == 'force_all':

    background_tasks: BackgroundTasks            # Force immediate retraining of all models

):            background_tasks.add_task(engine.force_retrain_all_models)

    """Trigger manual retraining of a specific model type."""        elif model_type == 'all':

    try:            background_tasks.add_task(engine.check_and_retrain_models)

        if model_type not in ['isolation_forest', 'temporal_autoencoder', 'all', 'force_all']:        else:

            raise HTTPException(            # Force retraining by clearing last training time

                status_code=status.HTTP_400_BAD_REQUEST,            engine.last_training_time[model_type] = datetime.min

                detail="Invalid model type. Must be 'isolation_forest', 'temporal_autoencoder', 'all', or 'force_all'"            background_tasks.add_task(engine.check_and_retrain_models)

            )        

                return {

        engine = get_ai_engine()            "message": f"Model retraining initiated for {model_type}",

                    "type": "force_retrain" if model_type == 'force_all' else "scheduled_retrain",

        # Trigger retraining in background            "timestamp": datetime.utcnow()

        if model_type == 'force_all':        }

            # Force immediate retraining of all models        

            background_tasks.add_task(engine.force_retrain_all_models)    except HTTPException:

        elif model_type == 'all':        raise

            background_tasks.add_task(engine.check_and_retrain_models)    except Exception as e:

        else:        logger.error(f"Error triggering retraining for {model_type}: {e}")

            # Force retraining by clearing last training time        raise HTTPException(

            engine.last_training_time[model_type] = datetime.min            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            background_tasks.add_task(engine.check_and_retrain_models)            detail="Failed to trigger model retraining"

                )

        return {

            "message": f"Model retraining initiated for {model_type}",

            "type": "force_retrain" if model_type == 'force_all' else "scheduled_retrain",@router.get("/training/status")

            "timestamp": datetime.utcnow()async def get_training_status():

        }    """Get detailed training status and schedule information."""

            try:

    except HTTPException:        engine = get_ai_engine()

        raise        current_time = datetime.utcnow()

    except Exception as e:        

        logger.error(f"Error triggering retraining for {model_type}: {e}")        training_status = {}

        raise HTTPException(        

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        for model_type in ['isolation_forest', 'temporal_autoencoder']:

            detail="Failed to trigger model retraining"            last_training = engine.last_training_time.get(model_type, datetime.min)

        )            seconds_since_training = (current_time - last_training).total_seconds()

            next_training_in = max(0, engine.retrain_interval - seconds_since_training)

            

@router.get("/training/status")            training_status[model_type] = {

async def get_training_status():                "last_trained": last_training.isoformat() if last_training != datetime.min else "never",

    """Get detailed training status and schedule information."""                "seconds_since_training": int(seconds_since_training),

    try:                "next_training_in_seconds": int(next_training_in),

        engine = get_ai_engine()                "training_interval": engine.retrain_interval,

        current_time = datetime.utcnow()                "is_due_for_training": seconds_since_training > engine.retrain_interval

                    }

        training_status = {}        

                return {

        for model_type in ['isolation_forest', 'temporal_autoencoder']:            "current_time": current_time.isoformat(),

            last_training = engine.last_training_time.get(model_type, datetime.min)            "training_status": training_status,

            seconds_since_training = (current_time - last_training).total_seconds()            "global_settings": {

            next_training_in = max(0, engine.retrain_interval - seconds_since_training)                "retrain_interval_seconds": engine.retrain_interval,

                            "min_data_points": engine.min_data_points,

            training_status[model_type] = {                "processing_frequency_seconds": 15

                "last_trained": last_training.isoformat() if last_training != datetime.min else "never",            }

                "seconds_since_training": int(seconds_since_training),        }

                "next_training_in_seconds": int(next_training_in),        

                "training_interval": engine.retrain_interval,    except HTTPException:

                "is_due_for_training": seconds_since_training > engine.retrain_interval        raise

            }    except Exception as e:

                logger.error(f"Error getting training status: {e}")

        return {        raise HTTPException(

            "current_time": current_time.isoformat(),            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            "training_status": training_status,            detail="Failed to get training status"

            "global_settings": {        )

                "retrain_interval_seconds": engine.retrain_interval,

                "min_data_points": engine.min_data_points,

                "processing_frequency_seconds": 15@router.get("/data/stats")

            }async def get_data_statistics(

        }    db: Session = Depends(get_db)

        ):

    except HTTPException:    """Get real-time data statistics for AI training."""

        raise    try:

    except Exception as e:        current_time = datetime.utcnow()

        logger.error(f"Error getting training status: {e}")        

        raise HTTPException(        # Get data counts for different time periods

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        stats = {

            detail="Failed to get training status"            "timestamp": current_time.isoformat(),

        )            "database_stats": {}

        }

        

@router.get("/data/stats")        # Location data statistics

async def get_data_statistics(        location_stats = {}

    db = Depends(get_supabase)        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:

):            cutoff_time = current_time - timedelta(hours=hours)

    """Get real-time data statistics for AI training."""            

    try:            location_count = db.query(Location).filter(

        current_time = datetime.utcnow()                Location.timestamp >= cutoff_time

                    ).count()

        # Get data counts for different time periods            

        stats = {            unique_tourists = db.query(Location.tourist_id).filter(

            "timestamp": current_time.isoformat(),                Location.timestamp >= cutoff_time

            "database_stats": {}            ).distinct().count()

        }            

                    location_stats[period_name] = {

        # Location data statistics                "location_updates": location_count,

        location_stats = {}                "unique_tourists": unique_tourists,

        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:                "avg_updates_per_tourist": round(location_count / max(unique_tourists, 1), 1)

            cutoff_time = (current_time - timedelta(hours=hours)).isoformat()            }

                    

            # Count locations        stats["database_stats"]["locations"] = location_stats

            location_response = db.table("locations") \        

                .select("*", count="exact") \        # Alert statistics

                .gte("timestamp", cutoff_time) \        alert_stats = {}

                .execute()        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:

            location_count = location_response.count            cutoff_time = current_time - timedelta(hours=hours)

                        

            # Count unique tourists            total_alerts = db.query(Alert).filter(

            unique_tourists_response = db.table("locations") \                Alert.timestamp >= cutoff_time

                .select("tourist_id", count="exact") \            ).count()

                .gte("timestamp", cutoff_time) \            

                .execute()            critical_alerts = db.query(Alert).filter(

            unique_tourists = len(set([loc.get("tourist_id") for loc in unique_tourists_response.data]))                Alert.timestamp >= cutoff_time,

                            Alert.severity == AlertSeverity.CRITICAL

            location_stats[period_name] = {            ).count()

                "location_updates": location_count,            

                "unique_tourists": unique_tourists,            alert_stats[period_name] = {

                "avg_updates_per_tourist": round(location_count / max(unique_tourists, 1), 1)                "total_alerts": total_alerts,

            }                "critical_alerts": critical_alerts

                    }

        stats["database_stats"]["locations"] = location_stats        

                stats["database_stats"]["alerts"] = alert_stats

        # Alert statistics        

        alert_stats = {}        # AI Assessment statistics

        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:        assessment_stats = {}

            cutoff_time = (current_time - timedelta(hours=hours)).isoformat()        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:

                        cutoff_time = current_time - timedelta(hours=hours)

            # Count all alerts            

            total_alerts_response = db.table("alerts") \            total_assessments = db.query(AIAssessment).filter(

                .select("*", count="exact") \                AIAssessment.created_at >= cutoff_time

                .gte("timestamp", cutoff_time) \            ).count()

                .execute()            

            total_alerts = total_alerts_response.count            critical_assessments = db.query(AIAssessment).filter(

                            AIAssessment.created_at >= cutoff_time,

            # Count critical alerts                AIAssessment.severity == AISeverity.CRITICAL

            critical_alerts_response = db.table("alerts") \            ).count()

                .select("*", count="exact") \            

                .gte("timestamp", cutoff_time) \            assessment_stats[period_name] = {

                .eq("severity", "CRITICAL") \                "total_assessments": total_assessments,

                .execute()                "critical_assessments": critical_assessments

            critical_alerts = critical_alerts_response.count            }

                    

            alert_stats[period_name] = {        stats["database_stats"]["ai_assessments"] = assessment_stats

                "total_alerts": total_alerts,        

                "critical_alerts": critical_alerts        # Active tourists

            }        active_tourists = db.query(Tourist).filter(

                    Tourist.is_active == True

        stats["database_stats"]["alerts"] = alert_stats        ).count()

                

        # AI Assessment statistics        stats["summary"] = {

        assessment_stats = {}            "active_tourists": active_tourists,

        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:            "data_freshness": "Real-time",

            cutoff_time = (current_time - timedelta(hours=hours)).isoformat()            "training_data_availability": "Sufficient" if location_stats["last_day"]["location_updates"] > 50 else "Limited"

                    }

            # Count all assessments        

            total_assessments_response = db.table("ai_assessments") \        return stats

                .select("*", count="exact") \        

                .gte("created_at", cutoff_time) \    except Exception as e:

                .execute()        logger.error(f"Error getting data statistics: {e}")

            total_assessments = total_assessments_response.count        raise HTTPException(

                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            # Count critical assessments            detail="Failed to get data statistics"

            critical_assessments_response = db.table("ai_assessments") \        )

                .select("*", count="exact") \

                .gte("created_at", cutoff_time) \

                .eq("severity", "CRITICAL") \@router.get("/analytics/dashboard")

                .execute()async def get_ai_analytics_dashboard(

            critical_assessments = critical_assessments_response.count    days: int = 7,

                db: Session = Depends(get_db)

            assessment_stats[period_name] = {):

                "total_assessments": total_assessments,    """Get AI analytics dashboard data."""

                "critical_assessments": critical_assessments    try:

            }        cutoff_time = datetime.utcnow() - timedelta(days=days)

                

        stats["database_stats"]["ai_assessments"] = assessment_stats        # Get assessment statistics

                total_assessments = db.query(AIAssessment).filter(

        # Active tourists            AIAssessment.created_at >= cutoff_time

        active_tourists_response = db.table("tourists") \        ).count()

            .select("*", count="exact") \        

            .eq("is_active", True) \        # Safety score distribution

            .execute()        safety_scores = db.query(AIAssessment.safety_score).filter(

        active_tourists = active_tourists_response.count            AIAssessment.created_at >= cutoff_time

                ).all()

        stats["summary"] = {        

            "active_tourists": active_tourists,        score_distribution = {

            "data_freshness": "Real-time",            "safe": len([s for s, in safety_scores if s[0] >= 80]),

            "training_data_availability": "Sufficient" if location_stats["last_day"]["location_updates"] > 50 else "Limited"            "warning": len([s for s, in safety_scores if 50 <= s[0] < 80]),

        }            "critical": len([s for s, in safety_scores if s[0] < 50])

                }

        return stats        

                # Model performance

    except Exception as e:        engine = get_ai_engine()

        logger.error(f"Error getting data statistics: {e}")        model_status = engine.get_model_status()

        raise HTTPException(        

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,        # Recent alerts triggered by AI

            detail="Failed to get data statistics"        ai_alerts_count = db.query(AIAssessment).filter(

        )            AIAssessment.created_at >= cutoff_time,

            AIAssessment.severity.in_(['WARNING', 'CRITICAL'])

        ).count()

@router.get("/analytics/dashboard")        

async def get_ai_analytics_dashboard(        return {

    days: int = 7,            "period_days": days,

    db = Depends(get_supabase)            "total_assessments": total_assessments,

):            "safety_score_distribution": score_distribution,

    """Get AI analytics dashboard data."""            "ai_alerts_triggered": ai_alerts_count,

    try:            "model_status": model_status,

        cutoff_time = (datetime.utcnow() - timedelta(days=days)).isoformat()            "dashboard_updated_at": datetime.utcnow()

                }

        # Get assessment statistics        

        total_assessments_response = db.table("ai_assessments") \    except HTTPException:

            .select("*", count="exact") \        raise

            .gte("created_at", cutoff_time) \    except Exception as e:

            .execute()        logger.error(f"Error getting AI analytics dashboard: {e}")

        total_assessments = total_assessments_response.count        raise HTTPException(

                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

        # Safety score distribution            detail="Failed to get analytics dashboard"

        safety_scores_response = db.table("ai_assessments") \        )

            .select("safety_score") \

            .gte("created_at", cutoff_time) \

            .execute()@router.post("/safety-score/recalculate/{tourist_id}")

        safety_scores = [score.get("safety_score") for score in safety_scores_response.data]async def recalculate_safety_score(

            tourist_id: int,

        score_distribution = {    background_tasks: BackgroundTasks,

            "safe": len([s for s in safety_scores if s >= 80]),    db: Session = Depends(get_db)

            "warning": len([s for s in safety_scores if 50 <= s < 80]),):

            "critical": len([s for s in safety_scores if s < 50])    """Recalculate safety score for a specific tourist using AI assessment."""

        }    try:

                # Verify tourist exists

        # Model performance        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()

        engine = get_ai_engine()        if not tourist:

        model_status = engine.get_model_status()            raise HTTPException(

                        status_code=status.HTTP_404_NOT_FOUND,

        # Recent alerts triggered by AI                detail="Tourist not found"

        ai_alerts_count_response = db.table("ai_assessments") \            )

            .select("*", count="exact") \        

            .gte("created_at", cutoff_time) \        # Trigger safety score recalculation

            .in_("severity", ["WARNING", "CRITICAL"]) \        safety_service = SafetyService(db)

            .execute()        background_tasks.add_task(

        ai_alerts_count = ai_alerts_count_response.count            safety_service.calculate_safety_score,

                    tourist_id

        return {        )

            "period_days": days,        

            "total_assessments": total_assessments,        return {

            "safety_score_distribution": score_distribution,            "message": "Safety score recalculation initiated",

            "ai_alerts_triggered": ai_alerts_count,            "tourist_id": tourist_id,

            "model_status": model_status,            "current_score": tourist.safety_score,

            "dashboard_updated_at": datetime.utcnow()            "timestamp": datetime.utcnow()

        }        }

                

    except HTTPException:    except HTTPException:

        raise        raise

    except Exception as e:    except Exception as e:

        logger.error(f"Error getting AI analytics dashboard: {e}")        logger.error(f"Error recalculating safety score for tourist {tourist_id}: {e}")

        raise HTTPException(        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail="Failed to get analytics dashboard"            detail="Failed to recalculate safety score"

        )        )





@router.post("/safety-score/recalculate/{tourist_id}")# Function to set the global AI engine (called from main.py)

async def recalculate_safety_score(def set_ai_engine(engine: AIEngineService):

    tourist_id: int,    global ai_engine

    background_tasks: BackgroundTasks,    ai_engine = engine
    db = Depends(get_supabase)
):
    """Recalculate safety score for a specific tourist using AI assessment."""
    try:
        adapter = SupabaseAdapter(db)
        
        # Verify tourist exists
        tourist = adapter.get_by_id("tourists", tourist_id)
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Get AI engine and request safety score recalculation
        engine = get_ai_engine()
        background_tasks.add_task(
            engine.safety_service.calculate_safety_score,
            tourist_id
        )
        
        return {
            "message": "Safety score recalculation initiated",
            "tourist_id": tourist_id,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating safety score for tourist {tourist_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate safety score"
        )