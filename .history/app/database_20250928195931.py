from supabase import create_client, Client
from app.config import settings
import logging
from typing import Generator

# For compatibility with existing code
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Initialize Supabase client (DIRECT CONNECTION - No SQLAlchemy)
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")

# SQLAlchemy setup for model compatibility
Base = declarative_base()
engine = create_engine("sqlite:///:memory:", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_supabase() -> Client:
    """
    Supabase dependency for FastAPI routes.
    Returns the global Supabase client instance.
    """
    return supabase


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI routes.
    Returns a SQLAlchemy session for model compatibility.
    This is only for compatibility with existing SQLAlchemy code.
    Actual operations should use Supabase client.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    Placeholder for table creation.
    Note: Actual data operations use Supabase which manages tables directly.
    """
    logger.info("📊 Using Supabase for database operations (no local tables needed)")
    return True