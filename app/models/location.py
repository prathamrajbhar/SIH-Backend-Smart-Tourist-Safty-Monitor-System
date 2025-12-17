"""
Location model definitions
"""
from typing import Dict, Any, Optional
from datetime import datetime

class Location:
    """
    Location model representation
    
    This class provides an object representation of tourist location data
    stored in the Supabase database.
    """
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.tourist_id = data.get("tourist_id")
        self.latitude = data.get("latitude")
        self.longitude = data.get("longitude")
        self.altitude = data.get("altitude")
        self.speed = data.get("speed")
        self.timestamp = data.get("timestamp") or datetime.utcnow().isoformat()
        self.accuracy = data.get("accuracy")
        self.battery_level = data.get("battery_level")
        self.source = data.get("source", "app")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "tourist_id": self.tourist_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "speed": self.speed,
            "timestamp": self.timestamp,
            "accuracy": self.accuracy,
            "battery_level": self.battery_level,
            "source": self.source
        }
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]):
        """Create a Location instance from database record"""
        if not data:
            return None
        return cls(data)