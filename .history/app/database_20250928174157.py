from supabase import create_client, Client
from app.config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Initialize Supabase client (DIRECT CONNECTION - No SQLAlchemy)
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")

# Define a placeholder for SQLAlchemy Base models
class Base:
    """
    Placeholder class for SQLAlchemy Base compatibility.
    This is just a placeholder to avoid import errors.
    """
    __tablename__: str = ""
    
    @classmethod
    def __declare_last__(cls):
        pass


# Session object for compatibility
class SessionLocal:
    """Placeholder for SQLAlchemy session compatibility"""
    pass


def get_supabase() -> Client:
    """
    Supabase dependency for FastAPI routes.
    Returns the global Supabase client instance.
    """
    return supabase


def get_db():
    """
    Legacy database dependency - returns Supabase client for compatibility.
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
    This function is kept for compatibility but does nothing.
    """
    logger.info("📊 Using Supabase managed tables - no local table creation needed")
    return True