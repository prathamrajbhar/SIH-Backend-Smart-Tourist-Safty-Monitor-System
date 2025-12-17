"""
Alert models for Smart Tourist Safety System
"""
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional


class AlertType(str, Enum):
    """Types of alerts in the system"""
    PANIC = "panic"
    GEOFENCE = "geofence"
    ANOMALY = "anomaly"
    TEMPORAL = "temporal"
    LOW_SAFETY_SCORE = "low_safety_score"
    SOS = "sos"
    MANUAL = "manual"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"


class Alert:
    """
    Alert model representation
    
    This class provides an object representation of alert data
    stored in the Supabase database.
    """
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.tourist_id = data.get("tourist_id")
        self.type = data.get("type")
        self.severity = data.get("severity")
        self.message = data.get("message")
        self.latitude = data.get("latitude")
        self.longitude = data.get("longitude")
        self.status = data.get("status", AlertStatus.ACTIVE)
        self.timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
        self.resolved_at = data.get("resolved_at")
        self.resolved_by = data.get("resolved_by")
        self.notes = data.get("notes", "")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "tourist_id": self.tourist_id,
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "timestamp": self.timestamp,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
            "notes": self.notes
        }
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]):
        """Create an Alert instance from database record"""
        if not data:
            return None
        return cls(data)