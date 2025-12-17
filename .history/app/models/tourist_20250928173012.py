from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from datetime import datetime
import enum


class Tourist:
    """
    Tourist model for Supabase.
    This class defines the structure and provides helper methods for tourists table.
    """
    table_name = "tourists"
    
    # Field definitions - used for documentation and reference
    fields = {
        "id": "bigint (PK, auto-generated)",
        "name": "varchar (required)",
        "contact": "varchar (required, unique)",
        "email": "varchar (optional)",
        "trip_info": "jsonb (default: {})",
        "emergency_contact": "varchar (required)",
        "safety_score": "integer (default: 100)",
        "age": "integer (optional)",
        "nationality": "varchar (default: Indian)",
        "passport_number": "varchar (optional)",
        "is_active": "boolean (default: true)",
        "last_location_update": "timestamptz (optional)",
        "created_at": "timestamptz (default: now())",
        "updated_at": "timestamptz (default: now())"
    }
    
    @staticmethod
    def default_values():
        """Return default values for tourist record"""
        return {
            "safety_score": 100,
            "nationality": "Indian",
            "is_active": True,
            "trip_info": {},
        }
    is_active = Column(Boolean, default=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    locations = relationship("Location", back_populates="tourist", cascade="all, delete-orphan")
    location_history = relationship("LocationHistory", back_populates="tourist", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="tourist", cascade="all, delete-orphan")
    ai_assessments = relationship("AIAssessment", back_populates="tourist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tourist(id={self.id}, name='{self.name}', safety_score={self.safety_score})>"