from supabase import create_client, Client
from app.config import settings
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")

# Initialize SQLAlchemy (hybrid approach - using both Supabase and SQLAlchemy)
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for SQLAlchemy models
Base = declarative_base()


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