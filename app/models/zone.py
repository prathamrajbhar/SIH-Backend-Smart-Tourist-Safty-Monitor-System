"""
Zone model definitions for restricted and safe zones
"""
from typing import Dict, Any, List
from enum import Enum

class ZoneType(str, Enum):
    RESTRICTED = "restricted"
    SAFE = "safe"

class RestrictedZone:
    """
    Restricted zone model representation
    
    This class provides an object representation of restricted zone data
    stored in the Supabase database.
    """
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.name = data.get("name")
        self.description = data.get("description")
        self.coordinates = data.get("coordinates", {})
        self.danger_level = data.get("danger_level", 1)  # 1-5 scale
        self.buffer_zone_meters = data.get("buffer_zone_meters", 100)
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.zone_type = ZoneType.RESTRICTED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates,
            "danger_level": self.danger_level,
            "buffer_zone_meters": self.buffer_zone_meters,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "zone_type": self.zone_type
        }
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]):
        """Create a RestrictedZone instance from database record"""
        if not data:
            return None
        return cls(data)

class SafeZone:
    """
    Safe zone model representation
    
    This class provides an object representation of safe zone data
    stored in the Supabase database.
    """
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.name = data.get("name")
        self.description = data.get("description")
        self.coordinates = data.get("coordinates", {})
        self.safety_level = data.get("safety_level", 1)  # 1-5 scale
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.zone_type = ZoneType.SAFE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates,
            "safety_level": self.safety_level,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "zone_type": self.zone_type
        }
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]):
        """Create a SafeZone instance from database record"""
        if not data:
            return None
        return cls(data)