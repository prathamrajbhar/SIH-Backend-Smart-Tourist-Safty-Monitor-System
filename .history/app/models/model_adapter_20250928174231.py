"""
Model adapter for Supabase integration.

This module provides compatibility functions to help transition
from SQLAlchemy ORM models to Supabase client.
"""

from typing import Dict, Any, Type, List, Optional
from supabase import Client
from pydantic import BaseModel


class ModelAdapter:
    """
    Adapter class to help with the transition from SQLAlchemy to Supabase.
    Provides methods that mimic SQLAlchemy querying but use Supabase under the hood.
    """
    
    @staticmethod
    def table_for_model(model_class) -> str:
        """Get the table name for a model class."""
        return model_class.__tablename__
    
    @staticmethod
    def from_orm(model_class, data: Dict[str, Any]):
        """
        Create a pseudo-ORM object from Supabase data.
        This allows existing code to treat the result like an ORM object.
        """
        if not data:
            return None
            
        # Create an instance of the model class
        instance = model_class()
        
        # Set attributes based on data dictionary
        for key, value in data.items():
            setattr(instance, key, value)
            
        return instance
    
    @staticmethod
    def from_orm_list(model_class, data_list: List[Dict[str, Any]]) -> List:
        """Convert a list of dictionaries to a list of pseudo-ORM objects."""
        return [ModelAdapter.from_orm(model_class, item) for item in data_list]
    
    @staticmethod
    async def query(supabase: Client, model_class, filters: Dict[str, Any] = None) -> List:
        """
        Query objects from Supabase and convert to pseudo-ORM objects.
        Mimics basic SQLAlchemy query functionality.
        """
        table_name = ModelAdapter.table_for_model(model_class)
        query = supabase.table(table_name).select("*")
        
        # Apply filters if provided
        if filters:
            for field, value in filters.items():
                query = query.eq(field, value)
                
        result = query.execute()
        
        # Convert to pseudo-ORM objects
        return ModelAdapter.from_orm_list(model_class, result.data)
    
    @staticmethod
    async def get_by_id(supabase: Client, model_class, id_value: Any):
        """Get a single record by ID."""
        table_name = ModelAdapter.table_for_model(model_class)
        result = supabase.table(table_name).select("*").eq("id", id_value).execute()
        
        if result.data and len(result.data) > 0:
            return ModelAdapter.from_orm(model_class, result.data[0])
        return None
    
    @staticmethod
    async def create(supabase: Client, model_class, data: Dict[str, Any]):
        """Create a new record."""
        table_name = ModelAdapter.table_for_model(model_class)
        result = supabase.table(table_name).insert(data).execute()
        
        if result.data and len(result.data) > 0:
            return ModelAdapter.from_orm(model_class, result.data[0])
        return None
    
    @staticmethod
    async def update(supabase: Client, model_class, id_value: Any, data: Dict[str, Any]):
        """Update an existing record."""
        table_name = ModelAdapter.table_for_model(model_class)
        result = supabase.table(table_name).update(data).eq("id", id_value).execute()
        
        if result.data and len(result.data) > 0:
            return ModelAdapter.from_orm(model_class, result.data[0])
        return None
    
    @staticmethod
    async def delete(supabase: Client, model_class, id_value: Any) -> bool:
        """Delete a record by ID."""
        table_name = ModelAdapter.table_for_model(model_class)
        result = supabase.table(table_name).delete().eq("id", id_value).execute()
        
        return len(result.data) > 0