from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
    def default_values() -> Dict[str, Any]:
        """Return default values for tourist record"""
        return {
            "safety_score": 100,
            "nationality": "Indian",
            "is_active": True,
            "trip_info": {},
        }
    @staticmethod
    def create_tourist(db, tourist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tourist in Supabase"""
        # Merge with default values
        data = {**Tourist.default_values(), **tourist_data}
        
        # Insert into Supabase
        result = db.table(Tourist.table_name).insert(data).execute()
        
        if len(result.data) > 0:
            logger.info(f"Created tourist: {result.data[0]['id']} - {result.data[0]['name']}")
            return result.data[0]
        else:
            logger.error("Failed to create tourist")
            return None
    
    @staticmethod
    def get_tourist_by_id(db, tourist_id: int) -> Optional[Dict[str, Any]]:
        """Get tourist by ID from Supabase"""
        result = db.table(Tourist.table_name).select("*").eq("id", tourist_id).execute()
        
        if len(result.data) > 0:
            return result.data[0]
        return None
    
    @staticmethod
    def get_tourist_by_contact(db, contact: str) -> Optional[Dict[str, Any]]:
        """Get tourist by contact number from Supabase"""
        result = db.table(Tourist.table_name).select("*").eq("contact", contact).execute()
        
        if len(result.data) > 0:
            return result.data[0]
        return None
    
    @staticmethod
    def update_tourist(db, tourist_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update tourist by ID in Supabase"""
        # Add updated_at timestamp
        data["updated_at"] = datetime.now().isoformat()
        
        result = db.table(Tourist.table_name).update(data).eq("id", tourist_id).execute()
        
        if len(result.data) > 0:
            logger.info(f"Updated tourist: {tourist_id}")
            return result.data[0]
        return None
    
    @staticmethod
    def get_all_tourists(db) -> List[Dict[str, Any]]:
        """Get all tourists from Supabase"""
        result = db.table(Tourist.table_name).select("*").execute()
        return result.data
    
    @staticmethod
    def delete_tourist(db, tourist_id: int) -> bool:
        """Delete tourist by ID from Supabase"""
        result = db.table(Tourist.table_name).delete().eq("id", tourist_id).execute()
        
        if len(result.data) > 0:
            logger.info(f"Deleted tourist: {tourist_id}")
            return True
        return False