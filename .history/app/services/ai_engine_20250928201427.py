import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import json
import pickle
from geopy.distance import geodesic

from app.database import get_db, get_supabase
from app.models import (
    Tourist, Location, Alert, AIAssessment, AIModelPrediction, 
    RestrictedZone, SafeZone, AlertType, AlertSeverity, AISeverity, AIModelName
)
from app.services.safety import SafetyService
from app.config import settings

logger = logging.getLogger(__name__)


class AIEngineService:
    """
    🤖 Hybrid AI Engine for Smart Tourist Safety System
    
    Implements complete pipeline:
    1. Rule-based Geo-fencing (instant alerts)
    2. Isolation Forest (anomaly detection)  
    3. Temporal Analysis (sequence modeling)
    4. Safety Scoring & Alert Fusion
    
    Features:
    - Continuous learning from Supabase data
    - Real-time assessment on location updates
    - Model versioning and performance tracking
    - Background processing for optimal performance
    """
    
    def __init__(self):
        self.db_session: Optional[Session] = None
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_versions: Dict[str, str] = {}
        self.performance_metrics: Dict[str, Dict] = {}
        
        # 🎯 Hybrid AI Configuration
        self.retrain_interval = 300   # Retrain every 5 minutes (more reasonable)
        self.min_data_points = 25     # Minimum for training (increased for better models)
        self.last_training_time = {}
        
        # 📊 Feature engineering configuration 
        self.feature_columns = [
            'distance_per_minute',     # Movement speed indicator
            'inactivity_duration',     # Time spent stationary  
            'deviation_from_route',    # Route adherence
            'speed_variance',          # Speed consistency
            'location_density',        # Area familiarity
            'zone_risk_score',         # Current zone safety
            'time_of_day_risk',        # Temporal risk factor
            'movement_consistency'     # Behavioral consistency
        ]
        
        # 🚨 Safety Score Thresholds
        self.safety_thresholds = {
            'safe': 80,       # >= 80 = Safe
            'warning': 50,    # 50-79 = Warning  
            'critical': 50    # < 50 = Critical
        }
        
        # 📁 Model storage
        self.model_dir = "models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize safety service
        self.safety_service = SafetyService()

    async def initialize(self):
        """🚀 Initialize the AI engine service."""
        try:
            logger.info("🤖 Initializing Hybrid AI Engine...")
            
            # Initialize database connection with optimizations
            self.db_session = SessionLocal()
            # Enable connection pooling optimizations
            self.db_session.execute("SET statement_timeout = '30s'")  # Prevent long-running queries
            self.db_session.execute("SET idle_in_transaction_session_timeout = '60s'")
            
            # Load existing models if available
            await self.load_models()
            
            # Initialize base models
            await self.initialize_models()
            
            # ✨ NEW: Immediately train models with fresh data on startup
            logger.info("🚀 Starting immediate model training with fresh data...")
            await self.force_retrain_all_models()
            
            # Start background tasks for continuous operation
            asyncio.create_task(self.continuous_training_loop())
            asyncio.create_task(self.real_time_assessment_loop())
            
            logger.info("✅ Hybrid AI Engine initialized successfully")
            logger.info("🎯 Active models: Geofencing + Isolation Forest + Temporal Analysis")
            logger.info("⚡ Training frequency: Every 5 minutes")
            logger.info("📡 Assessment frequency: Every 15 seconds")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Engine Service: {e}")
            raise

    async def initialize_models(self):
        """Initialize base AI models."""
        try:
            # 1. Rule-based Geofencing (always active, no training needed)
            self.models['geofence'] = {
                'type': 'rule_based',
                'version': '1.0.0',
                'initialized': True
            }
            
            # 2. Isolation Forest for Anomaly Detection  
            self.models['isolation_forest'] = IsolationForest(
                contamination=0.1,          # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            
            # 3. Temporal Analysis (simplified autoencoder approach)
            self.models['temporal'] = {
                'type': 'temporal_analysis',
                'window_size': 10,          # Last 10 location points
                'version': '1.0.0'
            }
            
            # 4. Initialize scalers
            self.scalers['features'] = StandardScaler()
            self.scalers['temporal'] = MinMaxScaler()
            
            logger.info("🎯 Base models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise

    async def continuous_training_loop(self):
        """🔄 Continuous loop for model retraining."""
        while True:
            try:
                await self.check_and_retrain_models()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in continuous training loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retry

    async def real_time_assessment_loop(self):
        """⚡ Continuous loop for real-time safety assessments."""
        while True:
            try:
                await self.process_recent_locations()
                await asyncio.sleep(15)  # Process every 15 seconds
            except Exception as e:
                logger.error(f"Error in real-time assessment loop: {e}")
                await asyncio.sleep(15)

    # ========================================================================
    # 🎯 HYBRID AI PIPELINE - Core Assessment Method
    # ========================================================================

    async def assess_tourist_safety(self, tourist_id: int, location_id: int) -> Dict[str, Any]:
        """
        🎯 Main hybrid AI assessment pipeline.
        
        Implements complete SafeHorizon AI approach:
        1. Rule-based Geo-fencing (instant)
        2. Isolation Forest (anomaly detection)
        3. Temporal Analysis (sequence modeling)  
        4. Safety Score Fusion
        
        Args:
            tourist_id: ID of tourist to assess
            location_id: ID of latest location record
            
        Returns:
            Complete AI assessment with safety score and recommendations
        """
        try:
            start_time = datetime.utcnow()
            logger.info(f"🤖 Starting AI assessment for tourist {tourist_id}")
            
            # Input validation
            if not isinstance(tourist_id, int) or tourist_id <= 0:
                raise ValueError(f"Invalid tourist_id: {tourist_id}")
            if not isinstance(location_id, int) or location_id <= 0:
                raise ValueError(f"Invalid location_id: {location_id}")
            
            # Get tourist and location data
            tourist = self.db_session.query(Tourist).filter(Tourist.id == tourist_id).first()
            location = self.db_session.query(Location).filter(Location.id == location_id).first()
            
            if not tourist or not location:
                raise ValueError(f"Tourist (id={tourist_id}) or location (id={location_id}) not found")
            
            # Initialize assessment results
            assessment_results = {
                'tourist_id': tourist_id,
                'location_id': location_id,
                'timestamp': start_time,
                'models_used': [],
                'predictions': {},
                'safety_score': 100,  # Start with perfect score
                'severity': 'SAFE',
                'confidence': 0.0,
                'alerts_triggered': [],
                'recommendations': []
            }
            
            # ========================================================================
            # 1️⃣ RULE-BASED GEO-FENCING (Highest Priority)
            # ========================================================================
            geofence_result = await self._assess_geofencing(location, tourist)
            assessment_results['models_used'].append('geofence')
            assessment_results['predictions']['geofence'] = geofence_result
            
            # Apply geofence penalties
            if geofence_result['restricted_zone']:
                assessment_results['safety_score'] -= 30  # Major penalty
                assessment_results['alerts_triggered'].append({
                    'type': 'GEOFENCE_VIOLATION',
                    'severity': 'HIGH',
                    'message': f"Tourist entered restricted zone: {geofence_result['zone_name']}"
                })
            
            # ========================================================================  
            # 2️⃣ ISOLATION FOREST (Anomaly Detection)
            # ========================================================================
            if 'isolation_forest' in self.models:
                anomaly_result = await self._assess_anomaly_detection(tourist_id, location)
                assessment_results['models_used'].append('isolation_forest')
                assessment_results['predictions']['isolation_forest'] = anomaly_result
                
                # Apply anomaly penalties
                anomaly_penalty = int(anomaly_result['anomaly_score'] * 25)  # Max 25 points
                assessment_results['safety_score'] -= anomaly_penalty
                
                if anomaly_result['is_anomaly']:
                    assessment_results['alerts_triggered'].append({
                        'type': 'ANOMALY_DETECTED',
                        'severity': 'MEDIUM',
                        'message': f"Unusual behavior detected (confidence: {anomaly_result['confidence']:.2f})"
                    })
            
            # ========================================================================
            # 3️⃣ TEMPORAL ANALYSIS (Sequence Modeling)
            # ========================================================================
            temporal_result = await self._assess_temporal_patterns(tourist_id, location)
            assessment_results['models_used'].append('temporal')
            assessment_results['predictions']['temporal'] = temporal_result
            
            # Apply temporal penalties
            temporal_penalty = int(temporal_result['risk_score'] * 20)  # Max 20 points
            assessment_results['safety_score'] -= temporal_penalty
            
            if temporal_result['pattern_deviation'] > 0.7:
                assessment_results['alerts_triggered'].append({
                    'type': 'TEMPORAL_ANOMALY', 
                    'severity': 'MEDIUM',
                    'message': f"Unusual movement pattern detected"
                })
            
            # ========================================================================
            # 4️⃣ SAFETY SCORE FUSION & FINAL ASSESSMENT
            # ========================================================================
            
            # Ensure score bounds
            assessment_results['safety_score'] = max(0, min(100, assessment_results['safety_score']))
            
            # Determine severity based on final score
            if assessment_results['safety_score'] >= self.safety_thresholds['safe']:
                assessment_results['severity'] = 'SAFE'
                assessment_results['recommendations'].append("Continue enjoying your trip safely!")
                
            elif assessment_results['safety_score'] >= self.safety_thresholds['warning']:
                assessment_results['severity'] = 'WARNING'  
                assessment_results['recommendations'].extend([
                    "Stay alert and avoid isolated areas",
                    "Keep emergency contacts updated",
                    "Consider returning to safe zones"
                ])
                
            else:
                assessment_results['severity'] = 'CRITICAL'
                assessment_results['recommendations'].extend([
                    "🚨 IMMEDIATE ACTION REQUIRED",
                    "Contact emergency services if needed", 
                    "Move to nearest safe location",
                    "Notify emergency contacts"
                ])
            
            # Calculate overall confidence
            model_confidences = [
                geofence_result.get('confidence', 1.0),
                assessment_results['predictions'].get('isolation_forest', {}).get('confidence', 0.5),
                temporal_result.get('confidence', 0.5)
            ]
            assessment_results['confidence'] = np.mean(model_confidences)
            
            # ========================================================================
            # 5️⃣ SAVE ASSESSMENT & UPDATE TOURIST SAFETY SCORE
            # ========================================================================
            
            # Save AI assessment to database
            ai_assessment = AIAssessment(
                tourist_id=tourist_id,
                location_id=location_id,
                safety_score=assessment_results['safety_score'],
                severity=assessment_results['severity'],
                geofence_alert=geofence_result['restricted_zone'],
                anomaly_score=assessment_results['predictions'].get('isolation_forest', {}).get('anomaly_score', 0.0),
                temporal_risk_score=temporal_result['risk_score'],
                confidence_level=assessment_results['confidence'],
                recommended_action='; '.join(assessment_results['recommendations'][:3]),
                model_versions={'hybrid_pipeline': '2.0.0'}
            )
            
            self.db_session.add(ai_assessment)
            
            # Update tourist safety score
            tourist.safety_score = assessment_results['safety_score']
            
            self.db_session.commit()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"✅ AI assessment completed for tourist {tourist_id}: "
                f"Score={assessment_results['safety_score']}, "
                f"Severity={assessment_results['severity']}, "
                f"Time={processing_time:.1f}ms"
            )
            
            return assessment_results
            
        except Exception as e:
            logger.error(f"❌ Error in AI assessment for tourist {tourist_id}: {e}", exc_info=True)
            if self.db_session:
                self.db_session.rollback()
            
            # Return safe fallback assessment instead of raising
            return {
                'tourist_id': tourist_id,
                'location_id': location_id if 'location_id' in locals() else 0,
                'timestamp': datetime.utcnow(),
                'models_used': ['fallback'],
                'predictions': {'error': str(e)},
                'safety_score': 50,  # Neutral score on error
                'severity': 'WARNING',
                'confidence': 0.0,
                'alerts_triggered': [],
                'recommendations': ['System error occurred - manual review recommended'],
                'error': True
            }

    # ========================================================================
    # 🛠️ HELPER METHODS FOR HYBRID PIPELINE
    # ========================================================================

    async def _assess_geofencing(self, location: Location, tourist: Tourist) -> Dict[str, Any]:
        """1️⃣ Rule-based geofencing assessment."""
        try:
            result = {
                'restricted_zone': False,
                'zone_name': '',
                'zone_type': '',
                'risk_level': 0,
                'confidence': 1.0  # Rule-based = 100% confidence
            }
            
            # Check if location is in restricted zone
            restricted_zones = self.db_session.query(RestrictedZone).filter(
                RestrictedZone.is_active == True
            ).all()
            
            for zone in restricted_zones:
                if self._point_in_polygon(location.latitude, location.longitude, zone.coordinates):
                    result['restricted_zone'] = True
                    result['zone_name'] = zone.name
                    result['zone_type'] = zone.zone_type
                    result['risk_level'] = zone.danger_level
                    break
            
            return result
            
        except Exception as e:
            logger.error(f"Error in geofencing assessment: {e}")
            return {'restricted_zone': False, 'confidence': 0.0}

    async def _assess_anomaly_detection(self, tourist_id: int, location: Location) -> Dict[str, Any]:
        """2️⃣ Isolation Forest anomaly detection."""
        try:
            result = {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0
            }
            
            if 'isolation_forest' not in self.models or 'isolation_forest' not in self.scalers:
                return result
            
            # Get recent location history for feature engineering (optimized query)
            recent_locations = self.db_session.query(Location).filter(
                and_(
                    Location.tourist_id == tourist_id,
                    Location.timestamp >= datetime.utcnow() - timedelta(hours=24)
                )
            ).order_by(Location.timestamp.desc()).limit(50).all()  # Limit to last 50 for performance
            
            if len(recent_locations) < 3:
                return result  # Not enough data
            
            # Engineer features
            features = await self._engineer_location_features(recent_locations, location)
            if not features or len(features) != len(self.feature_columns):
                logger.warning(f"Feature engineering failed for tourist {tourist_id}")
                return result
            
            # Scale features using the stored scaler
            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scalers['isolation_forest'].transform(features_array)
            
            # Make prediction
            model = self.models['isolation_forest']
            if hasattr(model, 'predict') and hasattr(model, 'score_samples'):
                prediction = model.predict(features_scaled)
                anomaly_score = model.score_samples(features_scaled)[0]
                
                result['is_anomaly'] = prediction[0] == -1
                # Normalize anomaly score: Isolation Forest scores are typically between -0.5 and 0.5
                # Convert to 0-1 scale where 1 = more anomalous
                normalized_score = max(0, min(1, (0.5 - anomaly_score) / 1.0))
                result['anomaly_score'] = normalized_score
                result['confidence'] = 0.85  # High confidence in ML prediction
            
            return result
            
        except Exception as e:
            logger.error(f"Error in anomaly detection for tourist {tourist_id}: {e}")
            return {'is_anomaly': False, 'anomaly_score': 0.0, 'confidence': 0.0}

    async def _assess_temporal_patterns(self, tourist_id: int, location: Location) -> Dict[str, Any]:
        """3️⃣ Temporal pattern analysis."""
        try:
            result = {
                'risk_score': 0.0,
                'pattern_deviation': 0.0,
                'confidence': 0.0
            }
            
            # Get location history for temporal analysis (optimized query)
            location_history = self.db_session.query(Location).filter(
                and_(
                    Location.tourist_id == tourist_id,
                    Location.timestamp >= datetime.utcnow() - timedelta(hours=6)
                )
            ).order_by(Location.timestamp.desc()).limit(30).all()  # Limit to last 30 for performance
            
            if len(location_history) < 5:
                return result  # Not enough temporal data
            
            # Analyze movement patterns
            distances = []
            time_intervals = []
            
            for i in range(1, len(location_history)):
                prev_loc = location_history[i-1]
                curr_loc = location_history[i]
                
                # Calculate distance
                distance = geodesic(
                    (prev_loc.latitude, prev_loc.longitude),
                    (curr_loc.latitude, curr_loc.longitude)
                ).kilometers
                
                # Calculate time interval
                time_diff = (curr_loc.timestamp - prev_loc.timestamp).total_seconds() / 3600  # hours
                
                distances.append(distance)
                time_intervals.append(max(time_diff, 0.01))  # Avoid division by zero
            
            # Calculate movement statistics
            speeds = [d/t for d, t in zip(distances, time_intervals)]
            avg_speed = np.mean(speeds) if speeds else 0.0
            speed_variance = np.var(speeds) if len(speeds) > 1 else 0.0
            
            # Calculate risk score based on temporal patterns
            risk_factors = []
            
            # Long inactivity risk (very slow movement consistently)
            if avg_speed < 0.5:  # Less than 0.5 km/h = essentially stationary
                inactivity_severity = min(1.0, (0.5 - avg_speed) / 0.5)  # Normalize
                risk_factors.append(0.4 * inactivity_severity)
            
            # Erratic movement risk (high speed variance)
            if speed_variance > 5:  # Lowered threshold for better sensitivity
                erratic_severity = min(1.0, speed_variance / 20)  # Normalize to 0-1
                risk_factors.append(0.3 * erratic_severity)
            
            # Time of day risk (higher risk at night)
            current_hour = location.timestamp.hour
            if current_hour < 6 or current_hour > 22:
                # More risk in deep night hours (midnight to 4 AM)
                night_risk = 0.3 if 0 <= current_hour <= 4 else 0.2
                risk_factors.append(night_risk)
            
            # Sudden speed changes (additional risk factor)
            if len(speeds) > 1:
                speed_changes = [abs(speeds[i] - speeds[i-1]) for i in range(1, len(speeds))]
                max_speed_change = max(speed_changes) if speed_changes else 0
                if max_speed_change > 10:  # Sudden speed change > 10 km/h
                    change_severity = min(1.0, max_speed_change / 50)  # Normalize
                    risk_factors.append(0.2 * change_severity)
            
            result['risk_score'] = min(1.0, sum(risk_factors))
            result['pattern_deviation'] = min(1.0, speed_variance / 15)  # Better normalization
            result['confidence'] = 0.75 if len(speeds) >= 3 else 0.5  # Confidence based on data quality
            
            return result
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {e}")
            return {'risk_score': 0.0, 'pattern_deviation': 0.0, 'confidence': 0.0}

    def _point_in_polygon(self, lat: float, lon: float, polygon_coords: Dict) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm."""
        try:
            if not polygon_coords or 'coordinates' not in polygon_coords:
                return False
            
            coords = polygon_coords['coordinates'][0]  # Assume first ring
            if not coords or len(coords) < 3:
                return False
            
            # Ray casting algorithm for point-in-polygon test
            x, y = lon, lat
            n = len(coords)
            inside = False
            
            p1x, p1y = coords[0][0], coords[0][1]
            for i in range(1, n + 1):
                p2x, p2y = coords[i % n][0], coords[i % n][1]
                if y > min(p1y, p2y):
                    if y <= max(p1y, p2y):
                        if x <= max(p1x, p2x):
                            if p1y != p2y:
                                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
                p1x, p1y = p2x, p2y
            
            return inside
            
        except Exception as e:
            logger.error(f"Error in point-in-polygon calculation: {e}")
            return False

    async def _calculate_zone_risk_score(self, location: Location) -> float:
        """Calculate zone risk score based on location's proximity to restricted/safe zones."""
        try:
            risk_score = 0.0
            lat, lon = float(location.latitude), float(location.longitude)
            
            # Check restricted zones
            restricted_zones = self.db_session.query(RestrictedZone).filter(
                RestrictedZone.is_active == True
            ).all()
            
            for zone in restricted_zones:
                if self._point_in_polygon(lat, lon, zone.coordinates):
                    # Inside restricted zone - high risk
                    risk_score = min(1.0, zone.danger_level / 10.0)  # Normalize danger_level to 0-1
                    break
            
            # Check safe zones (lower risk)
            if risk_score == 0.0:  # Only check if not in restricted zone
                safe_zones = self.db_session.query(SafeZone).filter(
                    SafeZone.is_active == True
                ).all()
                
                for zone in safe_zones:
                    if self._point_in_polygon(lat, lon, zone.coordinates):
                        risk_score = 0.1  # Low risk in safe zones
                        break
                else:
                    # Not in any zone - medium risk
                    risk_score = 0.3
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Error calculating zone risk score: {e}")
            return 0.3  # Default medium risk on error

    def _calculate_route_deviation(self, location_history: List[Location]) -> float:
        """Calculate route deviation based on path straightness and expected patterns."""
        try:
            if len(location_history) < 3:
                return 0.0  # Need at least 3 points to calculate deviation
            
            # Calculate the theoretical straight-line distance vs actual path distance
            start_point = location_history[0]
            end_point = location_history[-1]
            
            # Straight-line distance
            straight_distance = geodesic(
                (start_point.latitude, start_point.longitude),
                (end_point.latitude, end_point.longitude)
            ).kilometers
            
            # Actual path distance
            actual_distance = 0.0
            for i in range(1, len(location_history)):
                prev_loc = location_history[i-1]
                curr_loc = location_history[i]
                actual_distance += geodesic(
                    (prev_loc.latitude, prev_loc.longitude),
                    (curr_loc.latitude, curr_loc.longitude)
                ).kilometers
            
            # Calculate deviation ratio
            if straight_distance < 0.01:  # Too close to calculate meaningful deviation
                return 0.0
            
            deviation_ratio = (actual_distance - straight_distance) / straight_distance
            
            # Normalize to 0-1 scale (higher values indicate more deviation)
            # A deviation ratio of 0.5 (50% longer than straight line) = 0.5 deviation score
            normalized_deviation = min(1.0, deviation_ratio)
            
            return max(0.0, normalized_deviation)
            
        except Exception as e:
            logger.error(f"Error calculating route deviation: {e}")
            return 0.0

    def _calculate_feature_importance(self, X_scaled: np.ndarray) -> np.ndarray:
        """Calculate feature importance using variance-based method."""
        try:
            # For Isolation Forest, we can use feature variance as a proxy for importance
            feature_variances = np.var(X_scaled, axis=0)
            # Normalize to sum to 1
            if np.sum(feature_variances) > 0:
                feature_importance = feature_variances / np.sum(feature_variances)
            else:
                feature_importance = np.ones(len(self.feature_columns)) / len(self.feature_columns)
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            return np.ones(len(self.feature_columns)) / len(self.feature_columns)

    async def _engineer_location_features(self, location_history: List[Location], current_location: Location) -> List[float]:
        """Engineer features from location history for anomaly detection."""
        try:
            if len(location_history) < 2:
                return [0.0] * len(self.feature_columns)
            
            # Calculate basic movement features
            distances = []
            speeds = []
            
            for i in range(1, len(location_history)):
                prev_loc = location_history[i-1] 
                curr_loc = location_history[i]
                
                distance = geodesic(
                    (prev_loc.latitude, prev_loc.longitude),
                    (curr_loc.latitude, curr_loc.longitude)
                ).kilometers
                
                time_diff = (curr_loc.timestamp - prev_loc.timestamp).total_seconds() / 3600
                speed = distance / max(time_diff, 0.01)
                
                distances.append(distance)
                speeds.append(speed)
            
            # Feature engineering with proper calculations
            avg_speed = np.mean(speeds) if speeds else 0.0
            speed_variance = np.var(speeds) if len(speeds) > 1 else 0.0
            
            # Calculate inactivity duration (consecutive slow movements)
            inactivity_count = sum(1 for s in speeds if s < 0.1)
            inactivity_duration = (inactivity_count / max(len(speeds), 1)) * 100  # Percentage
            
            # Calculate location density (unique locations visited)
            unique_locations = len(set((round(float(loc.latitude), 3), round(float(loc.longitude), 3)) 
                                     for loc in location_history))
            location_density = min(unique_locations / max(len(location_history), 1) * 10, 10)  # Normalize to 0-10
            
            # Time of day risk (0-1 scale, higher at night)
            hour = current_location.timestamp.hour
            time_risk = 0.8 if 0 <= hour <= 5 or 22 <= hour <= 23 else 0.2
            
            # Movement consistency (inverse of normalized speed variance)
            movement_consistency = max(0, 1.0 - min(speed_variance / 10, 1.0))
            
            # Calculate zone risk score based on current location
            zone_risk = await self._calculate_zone_risk_score(current_location)
            
            # Calculate route deviation
            route_deviation = self._calculate_route_deviation(location_history)
            
            features = [
                avg_speed,                    # distance_per_minute (km/h)
                inactivity_duration,          # inactivity_duration (percentage)
                route_deviation,             # deviation_from_route
                speed_variance,              # speed_variance
                location_density,            # location_density (normalized)
                zone_risk,                   # zone_risk_score
                time_risk,                   # time_of_day_risk
                movement_consistency         # movement_consistency
            ]
            
            return features[:len(self.feature_columns)]
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return [0.0] * len(self.feature_columns)

    async def fetch_training_data(self, model_type: str, days_back: int = 7) -> pd.DataFrame:
        """Fetch training data from Supabase for the specified model type."""
        try:
            # Get cutoff time
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            logger.info(f"📈 Fetching {model_type} training data from {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} onwards...")
            
            if model_type == "isolation_forest":
                # Fetch location and tourist data for anomaly detection
                query = self.db_session.query(
                    Location.id,
                    Location.tourist_id,
                    Location.latitude,
                    Location.longitude,
                    Location.speed,
                    Location.timestamp,
                    Tourist.safety_score,
                    Alert.type.label('alert_type')
                ).join(
                    Tourist, Location.tourist_id == Tourist.id
                ).outerjoin(
                    Alert, 
                    (Alert.tourist_id == Location.tourist_id) & 
                    (func.date(Alert.timestamp) == func.date(Location.timestamp))
                ).filter(
                    Location.timestamp >= cutoff_time
                ).order_by(Location.timestamp.desc()).limit(5000)  # Limit training data for performance
                
            elif model_type == "temporal_autoencoder":
                # Fetch sequential location data for temporal analysis
                query = self.db_session.query(
                    Location.tourist_id,
                    Location.latitude,
                    Location.longitude,
                    Location.speed,
                    Location.timestamp,
                    Tourist.safety_score
                ).join(
                    Tourist, Location.tourist_id == Tourist.id
                ).filter(
                    Location.timestamp >= cutoff_time
                ).order_by(Location.tourist_id, Location.timestamp).limit(5000)  # Limit training data for performance
                
            else:
                logger.error(f"❌ Unknown model type: {model_type}")
                return pd.DataFrame()
            
            # Execute query and create DataFrame
            start_time = datetime.utcnow()
            results = query.all()
            query_time = (datetime.utcnow() - start_time).total_seconds()
            
            if not results:
                logger.warning(f"⚠️ No data found for {model_type} training (last {days_back} days)")
                return pd.DataFrame()
            
            # Convert to DataFrame
            columns = [column['name'] for column in query.statement.columns]
            df = pd.DataFrame(results, columns=columns)
            
            # Data quality metrics
            unique_tourists = df['tourist_id'].nunique() if 'tourist_id' in df.columns else 0
            date_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600 if 'timestamp' in df.columns else 0
            
            logger.info(f"✅ Fetched {len(df)} records for {model_type} in {query_time:.2f}s")
            logger.info(f"📉 Data quality: {unique_tourists} tourists, {date_range:.1f} hours span")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching training data for {model_type}: {e}")
            return pd.DataFrame()

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw location data."""
        try:
            if df.empty:
                return df
                
            # Sort by tourist_id and timestamp
            df = df.sort_values(['tourist_id', 'timestamp']).copy()
            
            # Initialize feature columns
            for col in self.feature_columns:
                df[col] = 0.0
            
            # Group by tourist to calculate features
            for tourist_id, group in df.groupby('tourist_id'):
                indices = group.index
                
                if len(group) < 2:
                    continue
                
                # Calculate distance per minute
                coords = group[['latitude', 'longitude']].values
                distances = []
                time_diffs = []
                
                for i in range(1, len(coords)):
                    # Haversine distance
                    lat1, lon1 = np.radians(coords[i-1])
                    lat2, lon2 = np.radians(coords[i])
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                    distance = 2 * 6371 * np.arcsin(np.sqrt(a))  # km
                    
                    time_diff = (group.iloc[i]['timestamp'] - group.iloc[i-1]['timestamp']).total_seconds() / 60  # minutes
                    
                    distances.append(distance)
                    time_diffs.append(max(time_diff, 0.1))  # Avoid division by zero
                
                # Distance per minute
                distance_per_min = [d/t for d, t in zip(distances, time_diffs)]
                df.loc[indices[1:], 'distance_per_minute'] = distance_per_min
                
                # Speed variance
                if 'speed' in group.columns:
                    speed_values = group['speed'].dropna()
                    if len(speed_values) > 1:
                        speed_var = speed_values.var()
                        df.loc[indices, 'speed_variance'] = speed_var
                
                # Inactivity duration (consecutive points with minimal movement)
                inactivity_durations = []
                current_inactivity = 0
                
                for i, dist_per_min in enumerate(distance_per_min):
                    if dist_per_min < 0.1:  # Less than 0.1 km/min (very slow)
                        current_inactivity += time_diffs[i]
                    else:
                        current_inactivity = 0
                    inactivity_durations.append(current_inactivity)
                
                df.loc[indices[1:], 'inactivity_duration'] = inactivity_durations
                
                # Location density (number of unique locations in last hour)
                for i, idx in enumerate(indices):
                    hour_ago = group.iloc[i]['timestamp'] - timedelta(hours=1)
                    recent_locations = group[group['timestamp'] >= hour_ago][['latitude', 'longitude']]
                    # Round to reduce precision and count unique locations
                    unique_locations = recent_locations.round(4).drop_duplicates()
                    df.loc[idx, 'location_density'] = len(unique_locations)
            
            # Alert frequency (alerts per day for each tourist)
            alert_counts = self.db_session.query(
                Alert.tourist_id,
                func.count(Alert.id).label('alert_count')
            ).filter(
                Alert.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).group_by(Alert.tourist_id).all()
            
            alert_dict = {tourist_id: count/7 for tourist_id, count in alert_counts}  # Alerts per day
            df['alert_frequency'] = df['tourist_id'].map(alert_dict).fillna(0)
            
            # Fill missing values
            df[self.feature_columns] = df[self.feature_columns].fillna(0)
            
            logger.info(f"Engineered features for {len(df)} data points")
            return df
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            return df

    async def train_isolation_forest(self, df: pd.DataFrame) -> bool:
        """Train the Isolation Forest model for anomaly detection."""
        try:
            if len(df) < self.min_data_points:
                logger.warning(f"Insufficient data for Isolation Forest training: {len(df)} < {self.min_data_points}")
                return False
            
            # Engineer features
            df_features = self.engineer_features(df)
            
            # Prepare training data
            X = df_features[self.feature_columns].values
            
            # Handle missing or infinite values
            X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train Isolation Forest
            model = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                n_jobs=-1
            )
            
            model.fit(X_scaled)
            
            # Evaluate on training data (for monitoring)
            predictions = model.predict(X_scaled)
            anomaly_ratio = (predictions == -1).mean()
            
            # Cross-validation for model performance
            validation_scores = []
            if len(X_scaled) >= 50:  # Only do cross-validation if enough data
                from sklearn.model_selection import cross_val_score
                cv_scores = cross_val_score(model, X_scaled, cv=3, scoring='neg_mean_squared_error')
                validation_scores = cv_scores.tolist()
            
            # Store model and scaler
            self.models['isolation_forest'] = model
            self.scalers['isolation_forest'] = scaler
            self.model_versions['isolation_forest'] = datetime.utcnow().isoformat()
            self.performance_metrics['isolation_forest'] = {
                'training_samples': len(X),
                'anomaly_ratio': float(anomaly_ratio),
                'validation_scores': validation_scores,
                'mean_validation_score': float(np.mean(validation_scores)) if validation_scores else None,
                'training_time': datetime.utcnow().isoformat(),
                'feature_importance': self._calculate_feature_importance(X_scaled).tolist()
            }
            
            # Save to disk
            model_path = os.path.join(self.model_dir, 'isolation_forest_model.joblib')
            scaler_path = os.path.join(self.model_dir, 'isolation_forest_scaler.joblib')
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            logger.info(f"Isolation Forest model trained successfully with {len(X)} samples, anomaly ratio: {anomaly_ratio:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Error training Isolation Forest model: {e}")
            return False

    async def train_temporal_model(self, df: pd.DataFrame) -> bool:
        """Train the temporal sequence model (simplified version)."""
        try:
            if len(df) < self.min_data_points:
                logger.warning(f"Insufficient data for temporal model training: {len(df)} < {self.min_data_points}")
                return False
            
            # For now, use a simple statistical model for temporal analysis
            # In production, this would be replaced with LSTM/GRU autoencoder
            
            df_features = self.engineer_features(df)
            
            # Calculate temporal patterns for each tourist
            temporal_features = []
            
            for tourist_id, group in df_features.groupby('tourist_id'):
                if len(group) < 5:  # Need at least 5 points for temporal analysis
                    continue
                
                # Calculate temporal metrics
                time_series = group.sort_values('timestamp')
                
                # Movement consistency
                distances = time_series['distance_per_minute'].values
                movement_variance = np.var(distances) if len(distances) > 1 else 0
                
                # Time pattern regularity
                time_diffs = [(time_series.iloc[i]['timestamp'] - time_series.iloc[i-1]['timestamp']).total_seconds() 
                             for i in range(1, len(time_series))]
                time_regularity = 1 / (1 + np.var(time_diffs)) if len(time_diffs) > 1 else 0
                
                temporal_features.append({
                    'tourist_id': tourist_id,
                    'movement_variance': movement_variance,
                    'time_regularity': time_regularity,
                    'avg_speed': distances.mean() if len(distances) > 0 else 0
                })
            
            if not temporal_features:
                logger.warning("No temporal features could be calculated")
                return False
            
            # Store temporal model (simplified statistical thresholds)
            temporal_df = pd.DataFrame(temporal_features)
            
            # Calculate thresholds based on percentiles
            thresholds = {
                'high_movement_variance': temporal_df['movement_variance'].quantile(0.9),
                'low_time_regularity': temporal_df['time_regularity'].quantile(0.1),
                'high_speed_variance': temporal_df['avg_speed'].quantile(0.95)
            }
            
            self.models['temporal_autoencoder'] = thresholds
            self.model_versions['temporal_autoencoder'] = datetime.utcnow().isoformat()
            self.performance_metrics['temporal_autoencoder'] = {
                'training_samples': len(temporal_df),
                'thresholds': thresholds,
                'training_time': datetime.utcnow().isoformat()
            }
            
            # Save to disk
            model_path = os.path.join(self.model_dir, 'temporal_model.json')
            with open(model_path, 'w') as f:
                json.dump({
                    'thresholds': thresholds,
                    'version': self.model_versions['temporal_autoencoder']
                }, f)
            
            logger.info(f"Temporal model trained successfully with {len(temporal_df)} tourist profiles")
            return True
            
        except Exception as e:
            logger.error(f"Error training temporal model: {e}")
            return False

    async def load_models(self):
        """Load existing models from disk."""
        try:
            # Load Isolation Forest
            model_path = os.path.join(self.model_dir, 'isolation_forest_model.joblib')
            scaler_path = os.path.join(self.model_dir, 'isolation_forest_scaler.joblib')
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                self.models['isolation_forest'] = joblib.load(model_path)
                self.scalers['isolation_forest'] = joblib.load(scaler_path)
                logger.info("Loaded Isolation Forest model from disk")
            
            # Load Temporal Model
            temporal_path = os.path.join(self.model_dir, 'temporal_model.json')
            if os.path.exists(temporal_path):
                with open(temporal_path, 'r') as f:
                    temporal_data = json.load(f)
                    self.models['temporal_autoencoder'] = temporal_data['thresholds']
                    self.model_versions['temporal_autoencoder'] = temporal_data['version']
                logger.info("Loaded temporal model from disk")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    async def force_retrain_all_models(self):
        """🔥 Force immediate retraining of all models with fresh data."""
        try:
            logger.info("🔥 FORCE RETRAINING: Starting immediate model training...")
            current_time = datetime.utcnow()
            
            for model_type in ['isolation_forest', 'temporal_autoencoder']:
                logger.info(f"📊 Force training {model_type} model...")
                
                # Fetch fresh training data (last 3 days for better training)
                df = await self.fetch_training_data(model_type, days_back=3)
                
                if not df.empty:
                    logger.info(f"📈 Fetched {len(df)} records for {model_type} force training")
                    
                    if model_type == 'isolation_forest':
                        success = await self.train_isolation_forest(df)
                    elif model_type == 'temporal_autoencoder':
                        success = await self.train_temporal_model(df)
                    
                    if success:
                        self.last_training_time[model_type] = current_time
                        logger.info(f"✅ Force training SUCCESSFUL for {model_type}")
                    else:
                        logger.error(f"❌ Force training FAILED for {model_type}")
                else:
                    logger.warning(f"⚠️ No data available for {model_type} force training")
                    
            logger.info("🎯 Force retraining completed for all models")
            
        except Exception as e:
            logger.error(f"💥 Error in force retraining: {e}")
            raise

    async def check_and_retrain_models(self):
        """Check if models need retraining and retrain if necessary."""
        try:
            current_time = datetime.utcnow()
            logger.info(f"🔄 Checking models for retraining at {current_time.strftime('%H:%M:%S')}")
            
            for model_type in ['isolation_forest', 'temporal_autoencoder']:
                last_training = self.last_training_time.get(model_type, datetime.min)
                seconds_since_training = (current_time - last_training).total_seconds()
                
                logger.info(f"📊 {model_type}: Last trained {seconds_since_training:.0f}s ago (threshold: {self.retrain_interval}s)")
                
                if seconds_since_training > self.retrain_interval:
                    logger.info(f"🚀 Starting retraining for {model_type} model...")
                    
                    # Fetch fresh training data
                    df = await self.fetch_training_data(model_type, days_back=1)  # Only last 1 day for faster processing
                    
                    if not df.empty:
                        logger.info(f"📈 Fetched {len(df)} records for {model_type} training")
                        
                        if model_type == 'isolation_forest':
                            success = await self.train_isolation_forest(df)
                        elif model_type == 'temporal_autoencoder':
                            success = await self.train_temporal_model(df)
                        
                        if success:
                            self.last_training_time[model_type] = current_time
                            logger.info(f"✅ Successfully retrained {model_type} model at {current_time.strftime('%H:%M:%S')}")
                        else:
                            logger.warning(f"❌ Failed to retrain {model_type} model")
                    else:
                        logger.warning(f"⚠️ No data available for {model_type} retraining")
                else:
                    logger.info(f"✋ {model_type} model is up-to-date (next training in {self.retrain_interval - seconds_since_training:.0f}s)")
                        
        except Exception as e:
            logger.error(f"❌ Error in model retraining check: {e}")

    async def predict_anomaly(self, tourist_id: int, location_data: Dict) -> Tuple[float, float]:
        """Predict anomaly score for a tourist's current location."""
        try:
            if 'isolation_forest' not in self.models:
                logger.warning("Isolation Forest model not available")
                return 0.0, 0.5  # Default: no anomaly, medium confidence
            
            # Get recent data for feature engineering
            recent_locations = self.db_session.query(Location).filter(
                Location.tourist_id == tourist_id,
                Location.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(Location.timestamp.desc()).limit(20).all()
            
            if not recent_locations:
                return 0.0, 0.3  # Low confidence due to lack of data
            
            # Create DataFrame for feature engineering
            location_records = []
            for loc in recent_locations:
                location_records.append({
                    'tourist_id': loc.tourist_id,
                    'latitude': float(loc.latitude),
                    'longitude': float(loc.longitude),
                    'speed': float(loc.speed) if loc.speed else 0,
                    'timestamp': loc.timestamp
                })
            
            df = pd.DataFrame(location_records)
            df_features = self.engineer_features(df)
            
            if df_features.empty or len(df_features) == 0:
                return 0.0, 0.3
            
            # Get the latest feature vector
            latest_features = df_features.iloc[-1][self.feature_columns].values.reshape(1, -1)
            
            # Handle missing values
            latest_features = np.nan_to_num(latest_features, nan=0.0, posinf=1e6, neginf=-1e6)
            
            # Scale features
            scaler = self.scalers.get('isolation_forest')
            if scaler:
                latest_features = scaler.transform(latest_features)
            
            # Predict
            model = self.models['isolation_forest']
            anomaly_score = model.decision_function(latest_features)[0]
            prediction = model.predict(latest_features)[0]
            
            # Convert to 0-1 score (higher = more anomalous)
            normalized_score = max(0, min(1, (0.5 - anomaly_score) / 1.0))
            confidence = 0.8  # High confidence in ML prediction
            
            return normalized_score, confidence
            
        except Exception as e:
            logger.error(f"Error predicting anomaly for tourist {tourist_id}: {e}")
            return 0.0, 0.1  # Low confidence due to error

    async def predict_temporal_risk(self, tourist_id: int) -> Tuple[float, float]:
        """Predict temporal risk score for a tourist."""
        try:
            if 'temporal_autoencoder' not in self.models:
                logger.warning("Temporal model not available")
                return 0.0, 0.5
            
            # Get recent movement data
            recent_locations = self.db_session.query(Location).filter(
                Location.tourist_id == tourist_id,
                Location.timestamp >= datetime.utcnow() - timedelta(hours=6)
            ).order_by(Location.timestamp.desc()).all()
            
            if len(recent_locations) < 3:
                return 0.0, 0.3  # Not enough data for temporal analysis
            
            # Calculate current temporal features
            location_records = []
            for loc in recent_locations:
                location_records.append({
                    'tourist_id': loc.tourist_id,
                    'latitude': float(loc.latitude),
                    'longitude': float(loc.longitude),
                    'speed': float(loc.speed) if loc.speed else 0,
                    'timestamp': loc.timestamp
                })
            
            df = pd.DataFrame(location_records)
            df_features = self.engineer_features(df)
            
            if df_features.empty:
                return 0.0, 0.3
            
            # Calculate temporal metrics
            distances = df_features['distance_per_minute'].values
            movement_variance = np.var(distances) if len(distances) > 1 else 0
            
            time_diffs = [(df.iloc[i]['timestamp'] - df.iloc[i-1]['timestamp']).total_seconds() 
                         for i in range(1, len(df))]
            time_regularity = 1 / (1 + np.var(time_diffs)) if len(time_diffs) > 1 else 0
            
            # Compare with thresholds
            thresholds = self.models['temporal_autoencoder']
            risk_score = 0.0
            
            if movement_variance > thresholds['high_movement_variance']:
                risk_score += 0.4
            
            if time_regularity < thresholds['low_time_regularity']:
                risk_score += 0.3
            
            # Check for recent inactivity
            recent_inactivity = df_features['inactivity_duration'].iloc[-1] if len(df_features) > 0 else 0
            if recent_inactivity > 120:  # More than 2 hours inactive
                risk_score += 0.3
            
            risk_score = min(1.0, risk_score)
            confidence = 0.7
            
            return risk_score, confidence
            
        except Exception as e:
            logger.error(f"Error predicting temporal risk for tourist {tourist_id}: {e}")
            return 0.0, 0.1

    async def process_recent_locations(self):
        """Process recent locations for real-time AI assessment."""
        try:
            # Get locations from the last 2 minutes that haven't been processed
            cutoff_time = datetime.utcnow() - timedelta(minutes=2)
            
            recent_locations = self.db_session.query(Location).outerjoin(
                AIAssessment, Location.id == AIAssessment.location_id
            ).filter(
                Location.timestamp >= cutoff_time,
                AIAssessment.id.is_(None)  # Not yet assessed
            ).order_by(Location.timestamp.desc()).limit(50).all()  # Process up to 50 locations at a time (reduced for performance)
            
            if recent_locations:
                logger.info(f"🔍 Processing {len(recent_locations)} recent locations for AI assessment...")
                
                for location in recent_locations:
                    await self.create_ai_assessment(location)
                    
                logger.info(f"✅ Completed processing {len(recent_locations)} locations")
            else:
                logger.debug(f"📍 No new locations to process (checked last 2 minutes)")
                
        except Exception as e:
            logger.error(f"❌ Error processing recent locations: {e}")

    async def create_ai_assessment(self, location: Location):
        """Create AI assessment for a location."""
        try:
            # Get geofence check
            safety_service = SafetyService(self.db_session)
            geofence_check = safety_service.check_location_safety(
                float(location.latitude), 
                float(location.longitude)
            )
            
            # Get AI predictions
            anomaly_score, anomaly_confidence = await self.predict_anomaly(
                location.tourist_id, 
                {
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude),
                    'timestamp': location.timestamp
                }
            )
            
            temporal_risk, temporal_confidence = await self.predict_temporal_risk(location.tourist_id)
            
            # Calculate overall safety score
            base_score = 100
            
            # Apply geofence penalty
            if geofence_check['in_restricted_zone']:
                base_score -= 30
                geofence_alert = True
            else:
                geofence_alert = False
            
            # Apply AI penalties
            base_score -= int(anomaly_score * 25)  # Up to -25 for anomalies
            base_score -= int(temporal_risk * 20)   # Up to -20 for temporal risk
            
            safety_score = max(0, min(100, base_score))
            
            # Determine severity
            if safety_score >= 80:
                severity = AISeverity.SAFE
                recommended_action = "No action required"
            elif safety_score >= 50:
                severity = AISeverity.WARNING
                recommended_action = "Monitor closely"
            else:
                severity = AISeverity.CRITICAL
                recommended_action = "Immediate intervention required"
            
            # Calculate overall confidence
            confidence_level = (anomaly_confidence + temporal_confidence) / 2
            
            # Create AI assessment
            assessment = AIAssessment(
                tourist_id=location.tourist_id,
                location_id=location.id,
                safety_score=safety_score,
                severity=severity,
                geofence_alert=geofence_alert,
                anomaly_score=anomaly_score,
                temporal_risk_score=temporal_risk,
                confidence_level=confidence_level,
                recommended_action=recommended_action,
                alert_message=f"AI Assessment: {severity.value} - Safety Score: {safety_score}",
                model_versions={
                    'isolation_forest': self.model_versions.get('isolation_forest', 'unknown'),
                    'temporal_autoencoder': self.model_versions.get('temporal_autoencoder', 'unknown')
                }
            )
            
            self.db_session.add(assessment)
            
            # Create individual model predictions
            predictions = [
                AIModelPrediction(
                    assessment_id=assessment.id,
                    model_name=AIModelName.ISOLATION_FOREST,
                    prediction_value=anomaly_score,
                    confidence=anomaly_confidence,
                    model_version=self.model_versions.get('isolation_forest', 'unknown')
                ),
                AIModelPrediction(
                    assessment_id=assessment.id,
                    model_name=AIModelName.TEMPORAL_AUTOENCODER,
                    prediction_value=temporal_risk,
                    confidence=temporal_confidence,
                    model_version=self.model_versions.get('temporal_autoencoder', 'unknown')
                )
            ]
            
            self.db_session.add_all(predictions)
            self.db_session.commit()
            
            # Update tourist safety score
            tourist = self.db_session.query(Tourist).filter(Tourist.id == location.tourist_id).first()
            if tourist:
                tourist.safety_score = safety_score
                self.db_session.commit()
            
            # Create alert if critical
            if severity == AISeverity.CRITICAL:
                from app.models import Alert
                alert = Alert(
                    tourist_id=location.tourist_id,
                    type=AlertType.ANOMALY,
                    severity=AlertSeverity.HIGH,
                    message=f"AI detected critical safety risk - Score: {safety_score}",
                    description=recommended_action,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    auto_generated=True,
                    ai_confidence=confidence_level
                )
                self.db_session.add(alert)
                self.db_session.commit()
                
                logger.warning(f"CRITICAL AI ALERT created for tourist {location.tourist_id}")
            
        except Exception as e:
            logger.error(f"Error creating AI assessment for location {location.id}: {e}")
            self.db_session.rollback()

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and performance metrics."""
        current_time = datetime.utcnow()
        
        # Calculate training status for each model
        training_status = {}
        for model_type in ['isolation_forest', 'temporal_autoencoder']:
            last_training = self.last_training_time.get(model_type, datetime.min)
            seconds_since_training = (current_time - last_training).total_seconds()
            
            training_status[model_type] = {
                "last_trained": last_training.isoformat() if last_training != datetime.min else "never",
                "seconds_ago": int(seconds_since_training),
                "next_training_in": max(0, int(self.retrain_interval - seconds_since_training)),
                "is_trained": model_type in self.models and self.models[model_type] is not None,
                "training_due": seconds_since_training > self.retrain_interval
            }
        
        return {
            "timestamp": current_time.isoformat(),
            "models_loaded": list(self.models.keys()),
            "model_versions": self.model_versions,
            "performance_metrics": self.performance_metrics,
            "training_status": training_status,
            "configuration": {
                "retrain_interval_seconds": self.retrain_interval,
                "min_data_points": self.min_data_points,
                "feature_columns": len(self.feature_columns),
                "safety_thresholds": self.safety_thresholds
            },
            "activity": {
                "processing_frequency": "Every 15 seconds",
                "training_frequency": "Every 60 seconds",
                "data_sources": ["locations", "tourists", "alerts"]
            }
        }