from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")


def get_supabase() -> Client:
    """
    Supabase dependency for FastAPI routes.
    Returns the global Supabase client instance.
    """
    return supabase


def get_db():
    """
    Database dependency - returns Supabase client.
    Used for consistency with existing code.
    """
    return supabase


async def check_db_connection() -> bool:
    """
    Check if Supabase connection is working.
    """
    try:
        # Test connection with a simple query
        result = supabase.table("tourists").select("count", count="exact").execute()
        logger.info("✅ Supabase connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        return False


async def create_tables():
    """
    Supabase tables are managed via Supabase dashboard.
    This function verifies that required tables exist.
    """
    try:
        # Check if key tables exist by querying them
        tables = ["tourists", "locations", "alerts", "safe_zones", "restricted_zones"]
        for table in tables:
            supabase.table(table).select("count", count="exact").limit(1).execute()
        
        logger.info("✅ Supabase tables verified successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error verifying Supabase tables: {e}")
        return False