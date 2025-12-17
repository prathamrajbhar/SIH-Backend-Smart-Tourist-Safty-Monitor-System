"""
Simple test for SafetyService with Supabase
This test directly imports only what's needed without relying on the entire model structure.
"""

import sys
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Only import what we need
from app.config import settings
from supabase import create_client

def test_safety_service_simple():
    """A simplified test for SafetyService that only uses Supabase directly."""
    
    try:
        logger.info("🧪 Starting simplified SafetyService test...")
        
        # Create Supabase client directly
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")
        
        # 1. Get a sample tourist
        tourist_response = supabase.table("tourists").select("*").limit(1).execute()
        if not tourist_response.data:
            logger.error("❌ No tourists found in database")
            return False
            
        tourist = tourist_response.data[0]
        tourist_id = tourist["id"]
        logger.info(f"✅ Found tourist: {tourist['name']} (ID: {tourist_id})")
        
        # 2. Test location coordinates
        test_coordinates = [
            {"latitude": 28.6139, "longitude": 77.2090, "name": "Delhi"},
            {"latitude": 15.2993, "longitude": 74.1240, "name": "Goa"},
            {"latitude": 34.0837, "longitude": 74.7973, "name": "Srinagar"}
        ]
        
        # 3. Add a test location for this tourist
        for coords in test_coordinates:
            location_data = {
                "tourist_id": tourist_id,
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            location_result = supabase.table("locations").insert(location_data).execute()
            logger.info(f"✅ Added test location for {coords['name']}: {location_result.data}")
        
        # 4. Test retrieving tourist's safety score
        safety_score_result = supabase.table("tourists").select("safety_score") \
            .eq("id", tourist_id).execute()
            
        if safety_score_result.data:
            current_score = safety_score_result.data[0].get("safety_score", 0)
            logger.info(f"✅ Current safety score for tourist {tourist_id}: {current_score}")
        
        # 5. Test updating safety score
        new_score = min(100, current_score + 5)  # Increase by 5 points
        update_result = supabase.table("tourists").update({"safety_score": new_score}) \
            .eq("id", tourist_id).execute()
            
        logger.info(f"✅ Updated safety score to {new_score}: {update_result.data}")
        
        # 6. Test creating an alert
        alert_data = {
            "tourist_id": tourist_id,
            "type": "manual",
            "severity": "LOW",
            "message": "Test alert from safety service test",
            "latitude": test_coordinates[0]["latitude"],
            "longitude": test_coordinates[0]["longitude"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "auto_generated": True
        }
        
        alert_result = supabase.table("alerts").insert(alert_data).execute()
        logger.info(f"✅ Created test alert: {alert_result.data}")
        
        logger.info("🎉 All basic Supabase operations for SafetyService tested successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_safety_service_simple()
    sys.exit(0 if success else 1)