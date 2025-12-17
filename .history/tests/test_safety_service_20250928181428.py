"""
Test script for the SafetyService using actual Supabase data.
This will test key functions like calculating safety scores, checking location safety,
and triggering automatic assessments.

Usage: python tests/test_safety_service.py
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.database import get_supabase
from app.services.safety import SafetyService
from app.services.supabase_utils import SupabaseError

def test_safety_service():
    """Test key functions of the SafetyService."""
    logger.info("🧪 Starting SafetyService tests with Supabase...")
    
    # Get Supabase client
    supabase = get_supabase()
    
    # Initialize SafetyService
    safety_service = SafetyService(supabase)
    
    # Step 1: Get a sample tourist to test with
    try:
        tourists_response = supabase.table("tourists").select("*").limit(1).execute()
        
        if not tourists_response.data:
            logger.error("❌ No tourists found in the database. Test failed.")
            return False
            
        sample_tourist = tourists_response.data[0]
        tourist_id = sample_tourist['id']
        logger.info(f"✅ Found sample tourist with ID: {tourist_id}")
        
        # Step 2: Test check_location_safety with sample coordinates (Delhi)
        delhi_location = {"latitude": 28.6139, "longitude": 77.2090}
        safety_check = safety_service.check_location_safety(
            delhi_location["latitude"], 
            delhi_location["longitude"]
        )
        logger.info(f"✅ Location safety check result: {safety_check}")
        
        # Step 3: Test calculate_safe_zone_duration
        safe_duration = safety_service.calculate_safe_zone_duration(tourist_id)
        logger.info(f"✅ Safe zone duration for tourist {tourist_id}: {safe_duration} hours")
        
        # Step 4: Test calculate_safety_score
        try:
            safety_score = safety_service.calculate_safety_score(tourist_id)
            logger.info(f"✅ Safety score calculation successful: {safety_score}")
        except Exception as e:
            logger.error(f"❌ Failed to calculate safety score: {str(e)}")
            return False
        
        # Step 5: Test trigger_automatic_assessment
        try:
            assessment = safety_service.trigger_automatic_assessment(tourist_id)
            logger.info(f"✅ Automatic assessment triggered: {assessment}")
        except Exception as e:
            logger.error(f"❌ Failed to trigger automatic assessment: {str(e)}")
            return False
            
        logger.info("🎉 All SafetyService tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_safety_service()
    sys.exit(0 if success else 1)