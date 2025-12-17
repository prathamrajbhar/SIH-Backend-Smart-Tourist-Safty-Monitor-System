from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class LocationCreate(BaseModel):
    tourist_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: Optional[float] = Field(None, ge=0)
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, lt=360)

    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        return float(v)


class LocationUpdate(BaseModel):
    tourist_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: Optional[float] = Field(None, ge=0)
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, lt=360)
    timestamp: Optional[datetime] = None


class LocationResponse(BaseModel):
    id: int
    tourist_id: int
    latitude: float
    longitude: float
    altitude: Optional[float]
    accuracy: Optional[float]
    speed: Optional[float]
    heading: Optional[float]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class LocationSummary(BaseModel):
    tourist_id: int
    tourist_name: str
    latitude: float
    longitude: float
    timestamp: datetime
    safety_score: int

    class Config:
        from_attributes = True