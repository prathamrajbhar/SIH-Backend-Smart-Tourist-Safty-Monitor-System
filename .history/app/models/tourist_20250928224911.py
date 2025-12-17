"""
Tourist model definitions
"""
from enum import Enum
from typing import Dict, Any

class Tourist:
    """
    Tourist model representation from database
    
    This class provides an object representation of tourist data
    stored in the Supabase database.
    """
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.name = data.get("name")
        self.contact = data.get("contact")
        self.email = data.get("email")
        self.emergency_contact = data.get("emergency_contact")
        self.trip_info = data.get("trip_info", {})
        self.safety_score = data.get("safety_score", 100)
        self.is_active = data.get("is_active", True)
        self.last_location_update = data.get("last_location_update")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.nationality = data.get("nationality", "Indian")
        self.age = data.get("age")
        self.passport_number = data.get("passport_number")
        self.current_location = None  # Will be populated separately when needed
    
    @property
    def safety_status(self) -> str:
        """Get safety status based on safety score"""
        if self.safety_score >= 80:
            return "SAFE"
        elif self.safety_score >= 50:
            return "WARNING"
        else:
            return "CRITICAL"
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "email": self.email,
            "emergency_contact": self.emergency_contact,
            "trip_info": self.trip_info,
            "safety_score": self.safety_score,
            "is_active": self.is_active,
            "last_location_update": self.last_location_update,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "nationality": self.nationality,
            "age": self.age,
            "passport_number": self.passport_number,
            "safety_status": self.safety_status
        }
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]):
        """Create a Tourist instance from database record"""
        if not data:
            return None
        return cls(data)