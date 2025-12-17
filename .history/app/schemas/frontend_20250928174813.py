from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime, date
from enum import Enum
from app.models.alert import AlertType, AlertSeverity


class TouristStatus(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"


class LocationCard(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime

    class Config:
        from_attributes = True


class TouristCard(BaseModel):
    id: int
    name: str
    contact: str
    safety_score: int
    status: TouristStatus
    last_location: Optional[LocationCard] = None
    recent_alerts_count: int = 0
    is_active: bool
    last_seen: datetime

    class Config:
        from_attributes = True


class AlertCard(BaseModel):
    id: int
    tourist_id: int
    tourist_name: str
    type: AlertType
    severity: AlertSeverity
    message: str
    location: Optional[LocationCard] = None
    timestamp: datetime
    auto_generated: bool
    acknowledged: bool

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_tourists: int
    active_tourists: int
    active_alerts: int
    critical_alerts: int
    avg_safety_score: float
    min_safety_score: int
    max_safety_score: int
    recent_location_updates: int
    last_updated: datetime


class SafetyMapData(BaseModel):
    tourist_locations: List[Dict[str, Any]]
    alert_locations: List[Dict[str, Any]]
    last_updated: datetime


class SafetyTrend(BaseModel):
    date: date
    total_alerts: int
    critical_alerts: int
    panic_alerts: int
    avg_safety_score: float
    total_assessments: int


class AlertStats(BaseModel):
    total_alerts: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    resolution_rate: float
    avg_resolution_time_hours: float
    period_days: int


class SystemHealth(BaseModel):
    overall_status: str
    database_status: str
    database_response_time: float
    ai_engine_status: str
    ai_models_loaded: List[str]
    recent_activity: Dict[str, int]
    last_checked: datetime


# Generic pagination wrapper
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


# API Response wrappers for consistent responses
class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Real-time data schemas
class LiveUpdate(BaseModel):
    type: str  # "location", "alert", "assessment"
    tourist_id: int
    data: Dict[str, Any]
    timestamp: datetime


class NotificationPayload(BaseModel):
    id: str
    type: str  # "alert", "safety_warning", "system"
    title: str
    message: str
    severity: str
    tourist_id: Optional[int] = None
    action_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Search and filter schemas
class TouristFilter(BaseModel):
    status: Optional[str] = None  # "active", "inactive", "critical"
    safety_score_min: Optional[int] = Field(None, ge=0, le=100)
    safety_score_max: Optional[int] = Field(None, ge=0, le=100)
    location_updated_since: Optional[datetime] = None
    has_active_alerts: Optional[bool] = None


class AlertFilter(BaseModel):
    severity: Optional[AlertSeverity] = None
    type: Optional[AlertType] = None
    tourist_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    acknowledged: Optional[bool] = None
    resolved: Optional[bool] = None


# Bulk operation schemas
class BulkTouristAction(BaseModel):
    tourist_ids: List[int] = Field(..., min_items=1, max_items=100)
    action: str  # "deactivate", "activate", "reset_safety_score"
    reason: Optional[str] = None


class BulkAlertAction(BaseModel):
    alert_ids: List[int] = Field(..., min_items=1, max_items=50)
    action: str  # "acknowledge", "resolve", "escalate"
    performed_by: str
    notes: Optional[str] = None


# Export schemas
class ExportRequest(BaseModel):
    format: str = Field(..., regex="^(csv|json|pdf)$")
    date_from: datetime
    date_to: datetime
    include_tourists: bool = True
    include_locations: bool = True
    include_alerts: bool = True
    include_assessments: bool = False


class ExportResponse(BaseModel):
    export_id: str
    status: str  # "processing", "completed", "failed"
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None


# WebSocket message schemas
class WSMessage(BaseModel):
    type: str
    channel: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSSubscription(BaseModel):
    channels: List[str]  # "alerts", "locations", "assessments", "system"
    tourist_ids: Optional[List[int]] = None  # Subscribe to specific tourists
    filters: Optional[Dict[str, Any]] = None


# Configuration schemas for frontend
class MapConfig(BaseModel):
    default_zoom: int = 10
    default_center: Dict[str, float] = {"lat": 28.6139, "lng": 77.2090}  # New Delhi
    max_markers: int = 500
    cluster_threshold: int = 20
    refresh_interval: int = 30  # seconds


class DashboardConfig(BaseModel):
    refresh_interval: int = 60  # seconds
    max_alerts_display: int = 50
    chart_data_points: int = 24
    auto_refresh_enabled: bool = True
    sound_alerts_enabled: bool = True


class NotificationConfig(BaseModel):
    enabled: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    notification_levels: List[str] = ["CRITICAL", "HIGH"]
