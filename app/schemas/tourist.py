from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class TouristCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    contact: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = None
    trip_info: Optional[Dict[str, Any]] = {}
    emergency_contact: str = Field(..., min_length=10, max_length=15)
    age: Optional[int] = Field(None, ge=0, le=150)
    nationality: Optional[str] = "Indian"
    passport_number: Optional[str] = None

    @validator('contact', 'emergency_contact')
    def validate_contact(cls, v):
        # Basic phone number validation
        import re
        if not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v


class TouristUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact: Optional[str] = Field(None, min_length=10, max_length=15)
    email: Optional[str] = None
    trip_info: Optional[Dict[str, Any]] = None
    emergency_contact: Optional[str] = Field(None, min_length=10, max_length=15)
    age: Optional[int] = Field(None, ge=0, le=150)
    nationality: Optional[str] = None
    passport_number: Optional[str] = None
    is_active: Optional[bool] = None


class TouristResponse(BaseModel):
    id: int
    name: str
    contact: str
    email: Optional[str]
    trip_info: Dict[str, Any]
    emergency_contact: str
    safety_score: int
    age: Optional[int]
    nationality: str
    passport_number: Optional[str]
    is_active: bool
    last_location_update: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TouristSummary(BaseModel):
    id: int
    name: str
    contact: str
    safety_score: int
    is_active: bool
    last_location_update: Optional[datetime]

    class Config:
        from_attributes = True