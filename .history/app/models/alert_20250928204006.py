"""
Alert models for Smart Tourist Safety System
"""
from enum import Enum
from datetime import datetime


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