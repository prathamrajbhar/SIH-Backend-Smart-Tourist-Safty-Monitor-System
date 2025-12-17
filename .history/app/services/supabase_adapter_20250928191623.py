"""
Supabase Adapter
---------------
This module provides a model-like interface for the Supabase client to make
it easier to transition from SQLAlchemy ORM to Supabase client.
"""

from typing import Dict, Any, List, Optional, Union, Type
import logging
from supabase import Client
from app.services.supabase_utils import safe_supabase_query, SupabaseError, safe_supabase_get

logger = logging.getLogger(__name__)

class SupabaseAdapter:
    """
    Adapter class to provide ORM-like methods for Supabase client
    """
    
    def __init__(self, db: Client):
        self.db = db
    
    def table_query(self, table_name: str):
        """Create a query builder for a specific table"""
        return self.db.table(table_name)
    
    def get_by_id(self, table_name: str, id_value: Union[int, str]) -> Optional[Dict]:
        """Get a record by its ID"""
        try:
            response = self.db.table(table_name).select("*").eq("id", id_value).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching {table_name} with id {id_value}: {str(e)}")
            return None
    
    def get_all(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all records from a table with pagination"""
        try:
            response = self.db.table(table_name).select("*").range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching all records from {table_name}: {str(e)}")
            return []
    
    def filter_by(self, table_name: str, **filters) -> List[Dict]:
        """Filter records by column values (similar to SQLAlchemy's filter_by)"""
        try:
            query = self.db.table(table_name).select("*")
            
    def count(self, table_name: str) -> int:
        """Count records in a table"""
        try:
            response = self.db.table(table_name).select("count", count="exact").execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            logger.error(f"Error counting records in {table_name}: {str(e)}")
            return 0
            
    def filter_by(self, table_name: str, **filters) -> List[Dict]:
        """Filter records by column values (similar to SQLAlchemy's filter_by)"""
        try:
            query = self.db.table(table_name).select("*")
            
            for column, value in filters.items():
                query = query.eq(column, value)
                
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error filtering {table_name} by {filters}: {str(e)}")
            return []
    
    def create(self, table_name: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new record"""
        try:
            response = self.db.table(table_name).insert(data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating record in {table_name}: {str(e)}")
            raise
    
    def update(self, table_name: str, id_value: Union[int, str], data: Dict[str, Any]) -> Optional[Dict]:
        """Update a record by ID"""
        try:
            response = self.db.table(table_name).update(data).eq("id", id_value).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating record in {table_name} with id {id_value}: {str(e)}")
            raise
    
    def delete(self, table_name: str, id_value: Union[int, str]) -> bool:
        """Delete a record by ID"""
        try:
            response = self.db.table(table_name).delete().eq("id", id_value).execute()
            return True if response.data else False
        except Exception as e:
            logger.error(f"Error deleting record from {table_name} with id {id_value}: {str(e)}")
            raise
    
    def count(self, table_name: str, **filters) -> int:
        """Count records in a table, optionally with filters"""
        try:
            query = self.db.table(table_name).select("*", count="exact")
            
            for column, value in filters.items():
                query = query.eq(column, value)
                
            response = query.execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            logger.error(f"Error counting records in {table_name}: {str(e)}")
            return 0