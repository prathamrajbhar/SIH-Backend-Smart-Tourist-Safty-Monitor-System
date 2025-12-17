from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models.alert import AlertType, AlertSeverity, AlertStatus


class AlertCreate(BaseModel):
    tourist_id: int
    type: AlertType
    message: str = Field(..., min_length=1)
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    severity: Optional[AlertSeverity] = AlertSeverity.LOW


class PanicAlertCreate(BaseModel):
    tourist_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    message: Optional[str] = "Panic button pressed - immediate assistance required!"


class GeofenceAlertCreate(BaseModel):
    tourist_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    zone_name: str
    message: Optional[str] = None


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledged: Optional[bool] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    tourist_id: int
    type: AlertType
    severity: AlertSeverity
    message: str
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    ai_confidence: Optional[float]
    auto_generated: bool
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    timestamp: datetime
    status: AlertStatus

    class Config:
        from_attributes = True


class AlertSummary(BaseModel):
    id: int
    tourist_id: int
    tourist_name: str
    type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    status: AlertStatus
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True