"""
🤖 Hybrid AI Engine for Smart Tourist Safety System

This module implements a comprehensive AI/ML hybrid pipeline for tourist safety assessment:
1. Rule-Based Geo-fencing - Check if location is inside restricted zones
2. Unsupervised Anomaly Detection - Using Isolation Forest
3. Temporal Modeling - Using LSTM/GRU Autoencoder concepts
4. Safety Score Calculation - Fusion of all models
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np
from geopy.distance import geodesic
import pandas as pd
from shapely.geometry import Point, Polygon
from sklearn.ensemble import IsolationForest
import json

from app.database import get_supabase, SupabaseSession

logger = logging.getLogger(__name__)

class AIEngineService:
    """
    🤖 Hybrid AI Engine for Smart Tourist Safety System
    
    Implements a multi-layer approach to safety assessment:
    1. Rule-based Geo-fencing (restricted zones)
    2. Unsupervised Anomaly Detection (Isolation Forest)
    3. Temporal Modeling (simplified time-series analysis)
    4. Alert Fusion and Safety Score Calculation
    """
    
    def __init__(self):
        self.supabase = get_supabase()
        self.initialized = False
        self.isolation_forest = None
        self.restricted_zones_cache = []
        self.last_cache_update = None
        self.cache_ttl = timedelta(minutes=5)  # Cache TTL for restricted zones
        
    async def initialize(self) -> bool:
        """Initialize the AI engine and prepare models"""
        try:
            # Test connection
            result = self.supabase.table("tourists").select("count", count="exact").execute()
            
            # Load and cache restricted zones
            await self._refresh_restricted_zones_cache()
            
            # Initialize isolation forest model
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                contamination=0.05,  # Expected proportion of anomalies
                random_state=42
            )
            
            # Flag as initialized
            self.initialized = True
            logger.info("✅ AI Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ AI Engine initialization failed: {e}")
            return False
    
    async def _refresh_restricted_zones_cache(self) -> None:
        """Refresh the cached restricted zones"""
        try:
            zones_result = self.supabase.table("restricted_zones").select("*").execute()
            self.restricted_zones_cache = zones_result.data
            self.last_cache_update = datetime.utcnow()
            logger.info(f"✅ Cached {len(self.restricted_zones_cache)} restricted zones")
        except Exception as e:
            logger.error(f"❌ Failed to cache restricted zones: {e}")
            self.restricted_zones_cache = []
    
    async def _get_tourist_recent_locations(self, tourist_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent locations for a tourist"""
        try:
            result = self.supabase.table("locations") \
                .select("*") \
                .eq("tourist_id", tourist_id) \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            
            # Reverse to get chronological order (oldest to newest)
            locations = list(reversed(result.data))
            return locations
        except Exception as e:
            logger.error(f"Error fetching recent locations: {e}")
            return []
    
    def _is_in_restricted_zone(self, latitude: float, longitude: float) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a point is inside any restricted zone using Shapely
        Returns (is_inside, zone_info) tuple
        """
        # Check if cache needs refresh
        if not self.last_cache_update or \
           datetime.utcnow() - self.last_cache_update > self.cache_ttl:
            logger.info("Restricted zones cache expired, but will use current data for this request")
        
        point = Point(longitude, latitude)  # GeoJSON uses (lon, lat) order
        
        for zone in self.restricted_zones_cache:
            try:
                # Parse the GeoJSON polygon
                if isinstance(zone.get("coordinates"), str):
                    # Parse JSON string if stored as string
                    coords_data = json.loads(zone.get("coordinates"))
                else:
                    coords_data = zone.get("coordinates")
                
                if not coords_data:
                    continue
                
                # Extract coordinates based on GeoJSON structure
                if "coordinates" in coords_data and isinstance(coords_data["coordinates"], list):
                    # Standard GeoJSON format
                    polygon_coords = coords_data["coordinates"][0]  # First polygon, outer ring
                elif isinstance(coords_data, list) and coords_data and isinstance(coords_data[0], list):
                    # Direct list of coordinates
                    polygon_coords = coords_data
                else:
                    logger.warning(f"Unsupported coordinates format for zone {zone.get('id')}")
                    continue
                
                # Create Shapely polygon - GeoJSON uses [lon, lat] format
                polygon = Polygon(polygon_coords)
                
                # Check if point is in polygon
                if polygon.contains(point):
                    return True, zone
                
                # Check if point is within buffer zone
                buffer_meters = zone.get("buffer_zone_meters", 100)
                if buffer_meters > 0:
                    # Create a buffer around the polygon and check if point is inside
                    # This is an approximation as we're not using geodesic distance
                    # For more accuracy, would need to convert meters to degrees appropriately
                    buffer_degrees = buffer_meters / 111000  # Rough conversion (1 degree ≈ 111 km)
                    buffered_polygon = polygon.buffer(buffer_degrees)
                    if buffered_polygon.contains(point):
                        return True, zone
            
            except (TypeError, KeyError, IndexError, json.JSONDecodeError) as e:
                logger.warning(f"Error processing zone {zone.get('id')}: {e}")
                continue
        
        return False, None
    
    def _extract_features(self, locations: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extract features from location history for anomaly detection:
        - Speed between consecutive points
        - Distance from average location
        - Directional change
        - Time gaps between updates
        """
        if not locations or len(locations) < 2:
            # Not enough data for feature extraction
            return np.array([])
        
        features = []
        
        # Create DataFrame from locations for easier processing
        df = pd.DataFrame(locations)
        
        # Convert timestamp strings to datetime objects if needed
        if df['timestamp'].dtype == object:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp to ensure chronological order
        df = df.sort_values('timestamp')
        
        # Calculate center point (average location)
        center_lat = df['latitude'].mean()
        center_lon = df['longitude'].mean()
        
        # Calculate features for each point (except the first one)
        for i in range(1, len(df)):
            # Current and previous positions
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Feature 1: Speed (m/s) - distance / time
            time_diff_seconds = (curr['timestamp'] - prev['timestamp']).total_seconds()
            if time_diff_seconds <= 0:
                speed = 0
            else:
                distance = geodesic(
                    (prev['latitude'], prev['longitude']),
                    (curr['latitude'], curr['longitude'])
                ).meters
                speed = distance / max(1, time_diff_seconds)  # Avoid division by zero
            
            # Feature 2: Distance from center point (m)
            dist_from_center = geodesic(
                (curr['latitude'], curr['longitude']),
                (center_lat, center_lon)
            ).meters
            
            # Feature 3: Time gap from previous update (seconds)
            time_gap = time_diff_seconds
            
            # Feature 4: Directional change
            # If we have at least 3 points, calculate the angle change
            if i >= 2:
                prev_prev = df.iloc[i-2]
                
                # Calculate vectors between points
                v1 = (prev['latitude'] - prev_prev['latitude'], 
                      prev['longitude'] - prev_prev['longitude'])
                v2 = (curr['latitude'] - prev['latitude'],
                      curr['longitude'] - prev['longitude'])
                
                # Calculate dot product and magnitudes
                dot_product = v1[0]*v2[0] + v1[1]*v2[1]
                mag_v1 = (v1[0]**2 + v1[1]**2) ** 0.5
                mag_v2 = (v2[0]**2 + v2[1]**2) ** 0.5
                
                # Calculate angle change (radians)
                if mag_v1 * mag_v2 > 0:
                    # Clamp the value to prevent domain errors
                    cosine = min(1, max(-1, dot_product / (mag_v1 * mag_v2)))
                    angle_change = np.arccos(cosine)
                else:
                    angle_change = 0
            else:
                angle_change = 0
            
            # Combine features
            feature_vector = [speed, dist_from_center, time_gap, angle_change]
            features.append(feature_vector)
        
        return np.array(features)
    
    def _detect_anomalies(self, features: np.ndarray) -> Tuple[List[float], float]:
        """
        Detect anomalies in the feature set using Isolation Forest
        Returns (anomaly_scores, average_score)
        """
        if features.size == 0 or len(features) < 2:
            # Not enough data for anomaly detection
            return [], 0
            
        try:
            # Fit the model and predict
            self.isolation_forest.fit(features)
            # Predict anomaly scores (-1 for anomalies, 1 for normal)
            raw_scores = self.isolation_forest.decision_function(features)
            
            # Convert to 0-1 scale (0 = anomaly, 1 = normal)
            # This conversion is based on the scikit-learn documentation
            anomaly_scores = (raw_scores + 0.5) / 2  # Now 0 to 1 (higher is better)
            
            # Calculate average score
            average_score = np.mean(anomaly_scores) if anomaly_scores.size > 0 else 0
            
            return anomaly_scores.tolist(), float(average_score)
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return [], 0
    
    def _analyze_temporal_patterns(self, locations: List[Dict[str, Any]]) -> float:
        """
        Simplified temporal analysis to detect unusual patterns over time
        Returns a temporal risk score (0-1, lower is better)
        """
        if not locations or len(locations) < 3:
            # Not enough data for temporal analysis
            return 0.0
            
        try:
            # Create DataFrame from locations
            df = pd.DataFrame(locations)
            
            # Convert timestamp strings to datetime objects if needed
            if df['timestamp'].dtype == object:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Sort by timestamp to ensure chronological order
            df = df.sort_values('timestamp')
            
            # Calculate time gaps between locations
            df['time_gap'] = df['timestamp'].diff().dt.total_seconds()
            
            # Calculate distances between consecutive points
            lats = df['latitude'].values
            lons = df['longitude'].values
            distances = []
            
            for i in range(1, len(df)):
                dist = geodesic(
                    (lats[i-1], lons[i-1]),
                    (lats[i], lons[i])
                ).meters
                distances.append(dist)
            
            # Add first distance as 0
            distances = [0] + distances
            df['distance'] = distances
            
            # Calculate speeds
            df['speed'] = np.where(df['time_gap'] > 0, df['distance'] / df['time_gap'], 0)
            
            # Detect unusual patterns:
            
            # 1. Unusual time gaps (too short or too long between updates)
            time_gaps = df['time_gap'].dropna().values
            time_gap_mean = np.mean(time_gaps)
            time_gap_std = max(1, np.std(time_gaps))  # Avoid division by zero
            time_gap_z_scores = np.abs((time_gaps - time_gap_mean) / time_gap_std)
            unusual_time_gaps = np.mean(time_gap_z_scores > 2)  # Z-score > 2 is unusual
            
            # 2. Unusual speeds (too fast or sudden stops)
            speeds = df['speed'].dropna().values
            speed_mean = np.mean(speeds)
            speed_std = max(1, np.std(speeds))  # Avoid division by zero
            speed_z_scores = np.abs((speeds - speed_mean) / speed_std)
            unusual_speeds = np.mean(speed_z_scores > 2)
            
            # 3. Unusual direction changes
            # Calculate bearing changes
            bearings = []
            for i in range(1, len(df) - 1):
                p1 = (lats[i-1], lons[i-1])
                p2 = (lats[i], lons[i])
                p3 = (lats[i+1], lons[i+1])
                
                # Calculate vectors
                v1 = (p2[0] - p1[0], p2[1] - p1[1])
                v2 = (p3[0] - p2[0], p3[1] - p2[1])
                
                # Calculate angle between vectors (simplified)
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                mag1 = np.sqrt(v1[0]**2 + v1[1]**2)
                mag2 = np.sqrt(v2[0]**2 + v2[1]**2)
                
                if mag1 * mag2 > 0:
                    # Clamp value to prevent domain errors
                    cos_angle = min(1, max(-1, dot / (mag1 * mag2)))
                    angle = np.arccos(cos_angle)
                    bearings.append(angle)
                else:
                    bearings.append(0)
            
            # Calculate unusual direction changes
            if bearings:
                bearing_mean = np.mean(bearings)
                bearing_std = max(0.1, np.std(bearings))  # Avoid division by zero
                bearing_z_scores = np.abs((bearings - bearing_mean) / bearing_std)
                unusual_bearings = np.mean(np.array(bearing_z_scores) > 2)
            else:
                unusual_bearings = 0
            
            # Combine factors into a temporal risk score (0-1, lower is better)
            temporal_risk = (unusual_time_gaps * 0.3 + 
                            unusual_speeds * 0.4 + 
                            unusual_bearings * 0.3)
            
            return min(1.0, max(0.0, temporal_risk))
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {e}")
            return 0.0
    
    async def process_location_update(self, tourist_id: int, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Process a new location update with the full AI/ML pipeline
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Step 1: Rule-Based Geo-fencing
            in_restricted_zone, zone = self._is_in_restricted_zone(latitude, longitude)
            
            # Step 2: Get tourist info and recent locations
            tourist_result = self.supabase.table("tourists").select("*").eq("id", tourist_id).execute()
            if not tourist_result.data:
                logger.error(f"Tourist not found: {tourist_id}")
                return {"error": "Tourist not found"}
            
            tourist = tourist_result.data[0]
            current_safety_score = tourist.get("safety_score", 100)
            
            # Get recent locations for advanced analysis
            recent_locations = await self._get_tourist_recent_locations(tourist_id)
            
            # Add current location to the list for analysis
            current_location = {
                "tourist_id": tourist_id,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.utcnow().isoformat()
            }
            locations_for_analysis = recent_locations + [current_location]
            
            # Safety assessment components
            assessment = {
                "tourist_id": tourist_id,
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.utcnow().isoformat(),
                "in_restricted_zone": in_restricted_zone,
            }
            
            # Additional details if in restricted zone
            if in_restricted_zone and zone:
                assessment.update({
                    "zone_name": zone.get("name", "Unknown Zone"),
                    "zone_type": zone.get("zone_type", "restricted"),
                    "danger_level": zone.get("danger_level", 3)
                })
            
            # Step 3: Unsupervised Anomaly Detection
            # Extract features from location history
            features = self._extract_features(locations_for_analysis)
            anomaly_scores, avg_anomaly_score = self._detect_anomalies(features)
            
            assessment["anomaly_score"] = avg_anomaly_score
            assessment["has_anomaly"] = avg_anomaly_score < 0.5  # Lower scores indicate anomalies
            
            # Step 4: Temporal Modeling
            temporal_risk = self._analyze_temporal_patterns(locations_for_analysis)
            assessment["temporal_risk"] = temporal_risk
            assessment["has_temporal_anomaly"] = temporal_risk > 0.7  # Higher risk is worse
            
            # Step 5: Alert Fusion and Safety Score Calculation
            # Calculate new safety score based on all factors
            new_safety_score = current_safety_score
            
            # Factor 1: Restricted Zone Impact
            if in_restricted_zone:
                danger_level = zone.get("danger_level", 3) if zone else 3
                reduction = min(danger_level * 10, 40)  # Max reduction 40 points
                new_safety_score = max(0, new_safety_score - reduction)
                logger.info(f"Restricted zone penalty: -{reduction} points")
                
                # Create geofence alert
                alert = {
                    "tourist_id": tourist_id,
                    "type": "geofence",
                    "severity": "HIGH" if danger_level >= 4 else "MEDIUM",
                    "message": f"Tourist entered restricted zone: {zone.get('name', 'Unknown')}",
                    "description": f"Danger level: {danger_level}/5",
                    "latitude": latitude,
                    "longitude": longitude,
                    "ai_confidence": 0.95,  # High confidence for geofencing
                    "auto_generated": True,
                    "status": "active",
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.supabase.table("alerts").insert(alert).execute()
                assessment["alert_created"] = True
                assessment["alert_type"] = "geofence"
            
            # Factor 2: Anomaly Detection Impact
            if avg_anomaly_score < 0.5:  # Anomaly detected
                anomaly_severity = 1.0 - avg_anomaly_score  # Convert to 0-1 severity
                reduction = int(anomaly_severity * 20)  # Max reduction 20 points
                new_safety_score = max(0, new_safety_score - reduction)
                logger.info(f"Anomaly penalty: -{reduction} points")
                
                # Create anomaly alert if severe enough
                if anomaly_severity > 0.7:
                    alert = {
                        "tourist_id": tourist_id,
                        "type": "anomaly",
                        "severity": "MEDIUM",
                        "message": "Unusual movement pattern detected",
                        "description": f"Anomaly confidence: {int(anomaly_severity * 100)}%",
                        "latitude": latitude,
                        "longitude": longitude,
                        "ai_confidence": anomaly_severity,
                        "auto_generated": True,
                        "status": "active",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self.supabase.table("alerts").insert(alert).execute()
                    assessment["alert_created"] = True
                    assessment["alert_type"] = "anomaly"
            
            # Factor 3: Temporal Risk Impact
            if temporal_risk > 0.7:  # High temporal risk
                reduction = int(temporal_risk * 15)  # Max reduction 15 points
                new_safety_score = max(0, new_safety_score - reduction)
                logger.info(f"Temporal risk penalty: -{reduction} points")
                
                # Create temporal alert
                alert = {
                    "tourist_id": tourist_id,
                    "type": "temporal",
                    "severity": "MEDIUM",
                    "message": "Unusual temporal movement pattern",
                    "description": f"Temporal risk factor: {int(temporal_risk * 100)}%",
                    "latitude": latitude,
                    "longitude": longitude,
                    "ai_confidence": temporal_risk,
                    "auto_generated": True,
                    "status": "active",
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.supabase.table("alerts").insert(alert).execute()
                assessment["alert_created"] = True
                assessment["alert_type"] = "temporal"
            
            # Factor 4: Safety Improvement over time (small increase for staying safe)
            if not in_restricted_zone and avg_anomaly_score > 0.8 and temporal_risk < 0.3:
                # Good behavior bonus
                new_safety_score = min(100, new_safety_score + 5)
                logger.info(f"Safety bonus: +5 points")
            
            # Update assessment with safety score info
            assessment["previous_safety_score"] = current_safety_score
            assessment["new_safety_score"] = new_safety_score
            assessment["safety_change"] = new_safety_score - current_safety_score
            
            # Set safety status based on score
            if new_safety_score > 80:
                assessment["safety_status"] = "SAFE"
            elif new_safety_score > 50:
                assessment["safety_status"] = "WARNING"
            else:
                assessment["safety_status"] = "CRITICAL"
                
                # Create low safety score alert for critical cases
                if new_safety_score < 40:
                    alert = {
                        "tourist_id": tourist_id,
                        "type": "low_safety_score",
                        "severity": "HIGH",
                        "message": "Critical safety score detected",
                        "description": f"Safety score dropped to {new_safety_score}",
                        "latitude": latitude,
                        "longitude": longitude,
                        "ai_confidence": 0.9,
                        "auto_generated": True,
                        "status": "active",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self.supabase.table("alerts").insert(alert).execute()
                    assessment["alert_created"] = True
                    assessment["alert_type"] = "low_safety_score"
            
            # Update tourist safety score in Supabase
            self.supabase.table("tourists").update({
                "safety_score": new_safety_score,
                "last_location_update": datetime.utcnow().isoformat()
            }).eq("id", tourist_id).execute()
            
            logger.info(f"AI Assessment completed for tourist {tourist_id} - Safety Score: {new_safety_score}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error in AI assessment: {e}")
            return {"error": str(e)}
    
    async def get_safety_assessment(self, tourist_id: int) -> Dict[str, Any]:
        """
        Get comprehensive safety assessment for a tourist
        """
        try:
            # Get tourist info
            tourist_result = self.supabase.table("tourists").select("*").eq("id", tourist_id).execute()
            if not tourist_result.data:
                return {"error": "Tourist not found"}
            
            tourist = tourist_result.data[0]
            safety_score = tourist.get("safety_score", 100)
            
            # Get active alerts
            alerts_result = self.supabase.table("alerts") \
                .select("*") \
                .eq("tourist_id", tourist_id) \
                .eq("status", "active") \
                .order("timestamp", desc=True) \
                .limit(5) \
                .execute()
            
            # Get recent locations
            locations_result = self.supabase.table("locations") \
                .select("*") \
                .eq("tourist_id", tourist_id) \
                .order("timestamp", desc=True) \
                .limit(10) \
                .execute()
            
            # Create comprehensive assessment
            assessment = {
                "tourist_id": tourist_id,
                "name": tourist.get("name"),
                "safety_score": safety_score,
                "safety_status": "SAFE" if safety_score > 80 else "WARNING" if safety_score > 50 else "CRITICAL",
                "active_alerts": len(alerts_result.data),
                "alerts": [
                    {
                        "id": alert.get("id"),
                        "type": alert.get("type"),
                        "severity": alert.get("severity"),
                        "message": alert.get("message"),
                        "timestamp": alert.get("timestamp"),
                    }
                    for alert in alerts_result.data[:3]  # Include top 3 most recent alerts
                ],
                "recent_locations": len(locations_result.data),
                "last_location": locations_result.data[0] if locations_result.data else None,
                "assessment_time": datetime.utcnow().isoformat()
            }
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error getting safety assessment: {e}")
            return {"error": str(e)}


# Global instance
ai_service = None

def set_ai_engine(service: AIEngineService) -> None:
    """Set the global AI engine instance"""
    global ai_service
    ai_service = service
    logger.info("Global AI engine instance has been set")

def get_ai_engine() -> AIEngineService:
    """Get the global AI engine instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIEngineService()
    return ai_service