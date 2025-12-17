from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client (DIRECT CONNECTION - No SQLAlchemy)
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")


def get_supabase() -> Client:
    """
    Supabase dependency for FastAPI routes.
    Returns the global Supabase client instance.
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
    Create SQLAlchemy tables for model compatibility.
    Note: Actual data operations use Supabase.
    """
    try:
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        logger.info("📊 SQLAlchemy tables created for model compatibility")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Table creation failed: {e}")
        return False