"""
AI Assessment & Safety Score API - Supabase Version
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import numpy as np
import json

from app.database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Safety Assessment"])

# Simplified AI models for demonstration
class IsolationForestModel:
    """Simple anomaly detection model using Isolation Forest approach"""
    
    def __init__(self):
        self.normal_speed_range = (0, 120)  # km/h
        self.normal_inactivity = 0  # hours
        
    def detect_anomaly(self, features):
        """
        Detect anomalies in tourist movement patterns
        
        Args:
            features: dict with speed, inactivity_duration, etc.
        
        Returns:
            anomaly_score: float between 0 and 1
            is_anomaly: boolean
        """
        score = 0.0
        speed = features.get("speed", 0)
        inactivity = features.get("inactivity_duration", 0)
        
        # Simple rule-based anomaly detection
        if speed > self.normal_speed_range[1]:
            score += min(1.0, (speed - self.normal_speed_range[1]) / 50)
            
        if inactivity > self.normal_inactivity:
            score += min(1.0, inactivity / 24)  # Scale by day
            
        is_anomaly = score > 0.7
        return score, is_anomaly


class TemporalModel:
    """Simple temporal model for movement pattern analysis"""
    
    def __init__(self):
        self.expected_check_in_frequency = 2  # hours
        
    def predict_risk(self, location_history):
        """
        Predict risk based on temporal movement patterns
        
        Args:
            location_history: list of location points with timestamps
            
        Returns:
            risk_score: float between 0 and 1
        """
        if not location_history:
            return 0.5  # Neutral score if no history
            
        # Calculate time gaps between location updates
        timestamps = [datetime.fromisoformat(loc.get("timestamp", loc.get("created_at"))) 
                     for loc in location_history if "timestamp" in loc or "created_at" in loc]
        
        if len(timestamps) < 2:
            return 0.3  # Low data points
            
        gaps = [(timestamps[i] - timestamps[i-1]).total_seconds() / 3600 
                for i in range(1, len(timestamps))]
        
        max_gap = max(gaps) if gaps else 0
        
        # Higher risk if large gaps in check-ins
        if max_gap > self.expected_check_in_frequency * 3:
            return min(1.0, max_gap / (self.expected_check_in_frequency * 5))
            
        return 0.1  # Low risk if regular updates


# Initialize models
isolation_forest = IsolationForestModel()
temporal_model = TemporalModel()


# ✅ Required Endpoint: /assessSafety
@router.post("/assessSafety", response_model=Dict[str, Any])
async def assess_safety_endpoint(
    tourist_id: int,
    latitude: float,
    longitude: float,
    speed: Optional[float] = None,
    timestamp: Optional[datetime] = None
):
    """
    Assess tourist safety based on current location and history.
    Required endpoint: /assessSafety
    """
    try:
        supabase = get_supabase()
        
        # Get tourist data
        tourist_result = supabase.table("tourists").select("*").eq("id", tourist_id).execute()
        
        if not tourist_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
            
        tourist = tourist_result.data[0]
        current_score = tourist.get("safety_score", 100)
        
        # Get location history (last 24 hours)
        now = datetime.utcnow()
        timestamp_24h_ago = (now - timedelta(hours=24)).isoformat()
        
        location_history = supabase.table("locations").select("*") \
            .eq("tourist_id", tourist_id) \
            .gt("timestamp", timestamp_24h_ago) \
            .order("timestamp", desc=True) \
            .execute()
            
        history = location_history.data
        
        # Check for geofence violations (restricted zones)
        zones_result = supabase.table("restricted_zones").select("*").execute()
        in_restricted_zone = False
        zone_danger = 0
        
        for zone in zones_result.data:
            try:
                coordinates_json = json.loads(zone["coordinates"])
                polygon_coords = coordinates_json["coordinates"][0]
                
                # Convert to (lat, lon) format for checking
                polygon = [(coord[1], coord[0]) for coord in polygon_coords]
                
                point = (latitude, longitude)
                if is_point_in_polygon(point, polygon):
                    in_restricted_zone = True
                    zone_danger = max(zone_danger, zone["danger_level"])
            except Exception as e:
                logger.error(f"Error checking zone {zone['id']}: {e}")
        
        # Calculate inactivity duration
        last_timestamp = None
        inactivity_duration = 0
        
        if history:
            try:
                last_location = history[0]
                last_timestamp_str = last_location.get("timestamp", last_location.get("created_at"))
                if last_timestamp_str:
                    last_timestamp = datetime.fromisoformat(last_timestamp_str)
                    inactivity_duration = (now - last_timestamp).total_seconds() / 3600  # in hours
            except Exception as e:
                logger.error(f"Error calculating inactivity: {e}")
        
        # Run anomaly detection
        features = {
            "speed": speed or 0,
            "inactivity_duration": inactivity_duration,
            "in_restricted_zone": in_restricted_zone,
            "zone_danger": zone_danger
        }
        
        anomaly_score, is_anomaly = isolation_forest.detect_anomaly(features)
        
        # Run temporal risk assessment
        temporal_risk = temporal_model.predict_risk(history)
        
        # Calculate combined safety score adjustment
        safety_adjustment = 0
        
        # Penalize for anomalies
        if is_anomaly:
            safety_adjustment -= int(20 * anomaly_score)
            
        # Penalize for restricted zones
        if in_restricted_zone:
            safety_adjustment -= zone_danger * 5
            
        # Penalize for temporal risk
        safety_adjustment -= int(15 * temporal_risk)
        
        # Reward for normal movement
        if not is_anomaly and not in_restricted_zone and temporal_risk < 0.3:
            safety_adjustment += 5
        
        # Ensure score stays in range 0-100
        new_score = max(0, min(100, current_score + safety_adjustment))
        
        # Update tourist safety score
        if new_score != current_score:
            supabase.table("tourists").update({
                "safety_score": new_score,
                "last_assessment": now.isoformat()
            }).eq("id", tourist_id).execute()
            
        # Create alert if high risk detected
        combined_risk = max(anomaly_score, temporal_risk)
        if combined_risk > 0.7 or (in_restricted_zone and zone_danger >= 4):
            alert_data = {
                "tourist_id": tourist_id,
                "type": "anomaly",
                "severity": "HIGH" if combined_risk > 0.8 else "MEDIUM",
                "message": f"AI Safety Alert: {'High' if combined_risk > 0.8 else 'Medium'} risk detected",
                "latitude": latitude,
                "longitude": longitude,
                "auto_generated": True,
                "status": "active",
                "timestamp": now.isoformat()
            }
            supabase.table("alerts").insert(alert_data).execute()
            
        return {
            "tourist_id": tourist_id,
            "previous_score": current_score,
            "new_score": new_score,
            "adjustment": safety_adjustment,
            "anomaly_score": float(anomaly_score),
            "temporal_risk": float(temporal_risk),
            "is_anomaly": is_anomaly,
            "in_restricted_zone": in_restricted_zone,
            "inactivity_hours": float(inactivity_duration),
            "timestamp": now.isoformat(),
            "risk_level": get_risk_level(new_score)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing safety: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess safety: {str(e)}"
        )


def get_risk_level(safety_score):
    """Determine risk level from safety score"""
    if safety_score >= 80:
        return "SAFE"
    elif safety_score >= 50:
        return "WARNING"
    else:
        return "CRITICAL"


# Helper function to check if a point is inside a polygon using ray-casting algorithm
def is_point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon using ray-casting algorithm
    
    Args:
        point: tuple (latitude, longitude)
        polygon: list of tuples [(lat1, lon1), (lat2, lon2), ...]
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


@router.get("/api/v1/safety/score/{tourist_id}", response_model=Dict[str, Any])
async def get_tourist_safety_score(tourist_id: int):
    """
    Get the current safety score and risk level for a tourist
    """
    try:
        supabase = get_supabase()
        
        result = supabase.table("tourists").select("id,name,safety_score,last_assessment").eq("id", tourist_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tourist not found"
            )
            
        tourist = result.data[0]
        safety_score = tourist.get("safety_score", 100)
        
        return {
            "tourist_id": tourist_id,
            "name": tourist.get("name", "Unknown"),
            "safety_score": safety_score,
            "risk_level": get_risk_level(safety_score),
            "last_assessed": tourist.get("last_assessment")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting safety score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get safety score"
        )