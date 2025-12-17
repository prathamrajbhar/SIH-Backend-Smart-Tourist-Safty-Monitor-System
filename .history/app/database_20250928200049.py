from supabase import create_client, Client
from app.config import settings
import logging
from typing import Generator, Any, Dict, List, Optional, Type
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
logger.info(f"🔗 Connected to Supabase: {settings.supabase_url}")

# Compatibility layer for SQLAlchemy code
class SupabaseSession:
    """A compatibility wrapper that mimics SQLAlchemy Session but uses Supabase"""
    
    def __init__(self):
        self.client = supabase
        self._tables_cache = {}
    
    def query(self, model_class):
        """Mimic SQLAlchemy query but return a SupabaseQuery instead"""
        table_name = getattr(model_class, '__tablename__', model_class.__name__.lower() + 's')
        return SupabaseQuery(self, table_name, model_class)
    
    def add(self, model):
        """Add a model instance to the database"""
        table_name = model.__class__.__tablename__
        # Extract attributes from model excluding SQLAlchemy special attributes
        data = {k: v for k, v in vars(model).items() if not k.startswith('_')}
        result = self.client.table(table_name).insert(data).execute()
        # Update model with returned data (including ID)
        if result.data:
            for k, v in result.data[0].items():
                setattr(model, k, v)
    
    def commit(self):
        """Commit changes (no-op in Supabase as changes are immediate)"""
        pass
    
    def rollback(self):
        """Rollback changes (limited support in Supabase)"""
        logger.warning("Rollback called but Supabase transactions are not fully supported")
    
    def refresh(self, model):
        """Refresh a model from the database"""
        table_name = model.__class__.__tablename__
        id_value = getattr(model, 'id', None)
        if id_value:
            result = self.client.table(table_name).select('*').eq('id', id_value).execute()
            if result.data:
                for k, v in result.data[0].items():
                    setattr(model, k, v)
    
    def close(self):
        """Close the session (no-op for Supabase)"""
        pass


class SupabaseQuery:
    """A compatibility wrapper that mimics SQLAlchemy Query but uses Supabase"""
    
    def __init__(self, session, table_name, model_class):
        self.session = session
        self.table_name = table_name
        self.model_class = model_class
        self.query = self.session.client.table(table_name).select('*')
        self._filters = []
    
    def filter(self, *conditions):
        """Add filter conditions"""
        for condition in conditions:
            # Extract column and value from condition
            if hasattr(condition, 'left') and hasattr(condition, 'right'):
                column = condition.left.name
                value = condition.right.value
                self.query = self.query.eq(column, value)
        return self
    
    def first(self):
        """Get first result"""
        result = self.query.limit(1).execute()
        if result.data:
            return self._create_model_instance(result.data[0])
        return None
    
    def all(self):
        """Get all results"""
        result = self.query.execute()
        return [self._create_model_instance(item) for item in result.data]
    
    def count(self):
        """Get count of results"""
        result = self.query.execute()
        return len(result.data)
    
    def _create_model_instance(self, data):
        """Create a model instance from data"""
        instance = self.model_class()
        for k, v in data.items():
            setattr(instance, k, v)
        return instance


# Base class for compatibility with SQLAlchemy models
class Base:
    """Base class for models that mimics SQLAlchemy's declarative base"""
    pass


def get_supabase() -> Client:
    """
    Supabase dependency for FastAPI routes.
    Returns the global Supabase client instance.
    """
    return supabase


def get_db() -> Generator[SupabaseSession, None, None]:
    """
    Database dependency for FastAPI routes.
    Returns a SupabaseSession that mimics SQLAlchemy session for compatibility.
    """
    db = SupabaseSession()
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
    Ensure tables exist in Supabase.
    Since we're using Supabase directly, tables should be created in the dashboard.
    This is just a placeholder to maintain compatibility.
    """
    logger.info("📊 Using Supabase for database operations (no local tables needed)")
    return True