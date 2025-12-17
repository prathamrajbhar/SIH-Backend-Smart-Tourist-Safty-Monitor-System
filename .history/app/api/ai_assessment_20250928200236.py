from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.database import get_db, get_supabase
from app.services.ai_engine_supabase import AIEngineService, get_ai_engine as get_global_ai_engine
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Assessment"])

# Use the global AI engine from ai_engine_supabase
def get_ai_engine() -> AIEngineService:
    """Get the global AI engine instance."""
    return get_global_ai_engine()


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


@router.get("/status")
async def get_ai_status():
    """Get AI engine status and model information."""
    try:
        engine = get_ai_engine()
        status_info = engine.get_model_status()
        
        return {
            "status": "active",
            "timestamp": datetime.utcnow(),
            **status_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI status"
        )


@router.post("/assess/{tourist_id}")
async def create_immediate_assessment(
    tourist_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create an immediate AI assessment for a specific tourist."""
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Get latest location
        latest_location = db.query(Location).filter(
            Location.tourist_id == tourist_id
        ).order_by(Location.timestamp.desc()).first()
        
        if not latest_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No location data found for tourist"
            )
        
        # Get AI engine and create assessment
        engine = get_ai_engine()
        
        # Run assessment in background
        background_tasks.add_task(
            engine.create_ai_assessment,
            latest_location
        )
        
        return {
            "message": "AI assessment initiated",
            "tourist_id": tourist_id,
            "location_id": latest_location.id,
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating immediate assessment for tourist {tourist_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create AI assessment"
        )


@router.get("/assessment/{tourist_id}")
async def get_tourist_assessments(
    tourist_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent AI assessments for a specific tourist."""
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Get assessments
        assessments = db.query(AIAssessment).filter(
            AIAssessment.tourist_id == tourist_id
        ).order_by(
            AIAssessment.created_at.desc()
        ).limit(limit).all()
        
        # Format response
        result = []
        for assessment in assessments:
            result.append({
                "id": assessment.id,
                "safety_score": assessment.safety_score,
                "severity": assessment.severity.value,
                "geofence_alert": assessment.geofence_alert,
                "anomaly_score": float(assessment.anomaly_score) if assessment.anomaly_score else None,
                "temporal_risk_score": float(assessment.temporal_risk_score) if assessment.temporal_risk_score else None,
                "confidence_level": float(assessment.confidence_level),
                "recommended_action": assessment.recommended_action,
                "alert_message": assessment.alert_message,
                "model_versions": assessment.model_versions,
                "created_at": assessment.created_at
            })
        
        return {
            "tourist_id": tourist_id,
            "assessments": result,
            "total_count": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessments for tourist {tourist_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI assessments"
        )


@router.get("/predictions/{assessment_id}")
async def get_model_predictions(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed model predictions for a specific assessment."""
    try:
        # Get assessment
        assessment = db.query(AIAssessment).filter(AIAssessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Get predictions
        predictions = db.query(AIModelPrediction).filter(
            AIModelPrediction.assessment_id == assessment_id
        ).all()
        
        # Format response
        prediction_details = []
        for pred in predictions:
            prediction_details.append({
                "id": pred.id,
                "model_name": pred.model_name.value,
                "prediction_value": float(pred.prediction_value),
                "confidence": float(pred.confidence),
                "processing_time_ms": float(pred.processing_time_ms) if pred.processing_time_ms else None,
                "model_version": pred.model_version,
                "metadata": pred.metadata,
                "created_at": pred.created_at
            })
        
        return {
            "assessment_id": assessment_id,
            "tourist_id": assessment.tourist_id,
            "overall_assessment": {
                "safety_score": assessment.safety_score,
                "severity": assessment.severity.value,
                "confidence_level": float(assessment.confidence_level),
                "recommended_action": assessment.recommended_action
            },
            "model_predictions": prediction_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions for assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model predictions"
        )


@router.post("/retrain/{model_type}")
async def trigger_model_retraining(
    model_type: str,
    background_tasks: BackgroundTasks
):
    """Trigger manual retraining of a specific model type."""
    try:
        if model_type not in ['isolation_forest', 'temporal_autoencoder', 'all', 'force_all']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid model type. Must be 'isolation_forest', 'temporal_autoencoder', 'all', or 'force_all'"
            )
        
        engine = get_ai_engine()
        
        # Trigger retraining in background
        if model_type == 'force_all':
            # Force immediate retraining of all models
            background_tasks.add_task(engine.force_retrain_all_models)
        elif model_type == 'all':
            background_tasks.add_task(engine.check_and_retrain_models)
        else:
            # Force retraining by clearing last training time
            engine.last_training_time[model_type] = datetime.min
            background_tasks.add_task(engine.check_and_retrain_models)
        
        return {
            "message": f"Model retraining initiated for {model_type}",
            "type": "force_retrain" if model_type == 'force_all' else "scheduled_retrain",
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retraining for {model_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger model retraining"
        )


@router.get("/training/status")
async def get_training_status():
    """Get detailed training status and schedule information."""
    try:
        engine = get_ai_engine()
        current_time = datetime.utcnow()
        
        training_status = {}
        
        for model_type in ['isolation_forest', 'temporal_autoencoder']:
            last_training = engine.last_training_time.get(model_type, datetime.min)
            seconds_since_training = (current_time - last_training).total_seconds()
            next_training_in = max(0, engine.retrain_interval - seconds_since_training)
            
            training_status[model_type] = {
                "last_trained": last_training.isoformat() if last_training != datetime.min else "never",
                "seconds_since_training": int(seconds_since_training),
                "next_training_in_seconds": int(next_training_in),
                "training_interval": engine.retrain_interval,
                "is_due_for_training": seconds_since_training > engine.retrain_interval
            }
        
        return {
            "current_time": current_time.isoformat(),
            "training_status": training_status,
            "global_settings": {
                "retrain_interval_seconds": engine.retrain_interval,
                "min_data_points": engine.min_data_points,
                "processing_frequency_seconds": 15
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get training status"
        )


@router.get("/data/stats")
async def get_data_statistics(
    db: Session = Depends(get_db)
):
    """Get real-time data statistics for AI training."""
    try:
        current_time = datetime.utcnow()
        
        # Get data counts for different time periods
        stats = {
            "timestamp": current_time.isoformat(),
            "database_stats": {}
        }
        
        # Location data statistics
        location_stats = {}
        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:
            cutoff_time = current_time - timedelta(hours=hours)
            
            location_count = db.query(Location).filter(
                Location.timestamp >= cutoff_time
            ).count()
            
            unique_tourists = db.query(Location.tourist_id).filter(
                Location.timestamp >= cutoff_time
            ).distinct().count()
            
            location_stats[period_name] = {
                "location_updates": location_count,
                "unique_tourists": unique_tourists,
                "avg_updates_per_tourist": round(location_count / max(unique_tourists, 1), 1)
            }
        
        stats["database_stats"]["locations"] = location_stats
        
        # Alert statistics
        alert_stats = {}
        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:
            cutoff_time = current_time - timedelta(hours=hours)
            
            total_alerts = db.query(Alert).filter(
                Alert.timestamp >= cutoff_time
            ).count()
            
            critical_alerts = db.query(Alert).filter(
                Alert.timestamp >= cutoff_time,
                Alert.severity == AlertSeverity.CRITICAL
            ).count()
            
            alert_stats[period_name] = {
                "total_alerts": total_alerts,
                "critical_alerts": critical_alerts
            }
        
        stats["database_stats"]["alerts"] = alert_stats
        
        # AI Assessment statistics
        assessment_stats = {}
        for period_name, hours in [("last_hour", 1), ("last_day", 24), ("last_week", 168)]:
            cutoff_time = current_time - timedelta(hours=hours)
            
            total_assessments = db.query(AIAssessment).filter(
                AIAssessment.created_at >= cutoff_time
            ).count()
            
            critical_assessments = db.query(AIAssessment).filter(
                AIAssessment.created_at >= cutoff_time,
                AIAssessment.severity == AISeverity.CRITICAL
            ).count()
            
            assessment_stats[period_name] = {
                "total_assessments": total_assessments,
                "critical_assessments": critical_assessments
            }
        
        stats["database_stats"]["ai_assessments"] = assessment_stats
        
        # Active tourists
        active_tourists = db.query(Tourist).filter(
            Tourist.is_active == True
        ).count()
        
        stats["summary"] = {
            "active_tourists": active_tourists,
            "data_freshness": "Real-time",
            "training_data_availability": "Sufficient" if location_stats["last_day"]["location_updates"] > 50 else "Limited"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting data statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data statistics"
        )


@router.get("/analytics/dashboard")
async def get_ai_analytics_dashboard(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get AI analytics dashboard data."""
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Get assessment statistics
        total_assessments = db.query(AIAssessment).filter(
            AIAssessment.created_at >= cutoff_time
        ).count()
        
        # Safety score distribution
        safety_scores = db.query(AIAssessment.safety_score).filter(
            AIAssessment.created_at >= cutoff_time
        ).all()
        
        score_distribution = {
            "safe": len([s for s, in safety_scores if s[0] >= 80]),
            "warning": len([s for s, in safety_scores if 50 <= s[0] < 80]),
            "critical": len([s for s, in safety_scores if s[0] < 50])
        }
        
        # Model performance
        engine = get_ai_engine()
        model_status = engine.get_model_status()
        
        # Recent alerts triggered by AI
        ai_alerts_count = db.query(AIAssessment).filter(
            AIAssessment.created_at >= cutoff_time,
            AIAssessment.severity.in_(['WARNING', 'CRITICAL'])
        ).count()
        
        return {
            "period_days": days,
            "total_assessments": total_assessments,
            "safety_score_distribution": score_distribution,
            "ai_alerts_triggered": ai_alerts_count,
            "model_status": model_status,
            "dashboard_updated_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI analytics dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics dashboard"
        )


@router.post("/safety-score/recalculate/{tourist_id}")
async def recalculate_safety_score(
    tourist_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Recalculate safety score for a specific tourist using AI assessment."""
    try:
        # Verify tourist exists
        tourist = db.query(Tourist).filter(Tourist.id == tourist_id).first()
        if not tourist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
        
        # Trigger safety score recalculation
        safety_service = SafetyService(db)
        background_tasks.add_task(
            safety_service.calculate_safety_score,
            tourist_id
        )
        
        return {
            "message": "Safety score recalculation initiated",
            "tourist_id": tourist_id,
            "current_score": tourist.safety_score,
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


# Function to set the global AI engine (called from main.py)
def set_ai_engine(engine: AIEngineService):
    global ai_engine
    ai_engine = engine