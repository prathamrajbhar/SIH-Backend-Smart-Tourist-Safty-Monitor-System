"""
Helper functions for handling common Supabase errors and response patterns.
Provides consistent error handling and logging for Supabase operations.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List, Union
import json
from supabase import Client

logger = logging.getLogger(__name__)

class SupabaseError(Exception):
    """Custom exception for Supabase-related errors with detailed context."""
    def __init__(self, message: str, operation: str, table: str = None, data: Any = None, original_error: Exception = None):
        self.operation = operation
        self.table = table
        self.data = data
        self.original_error = original_error
        super().__init__(message)


def safe_supabase_query(func):
    """
    Decorator for safely handling Supabase queries and providing detailed error information.
    
    Example usage:
    
    @safe_supabase_query
    def get_tourist(db: Client, tourist_id: int):
        return db.table("tourists").select("*").eq("id", tourist_id).execute()
    """
    def wrapper(*args, **kwargs):
        try:
            # Extract operation details for better logging
            operation_name = func.__name__
            
            # Execute the wrapped function
            result = func(*args, **kwargs)
            
            # Check if result contains error
            if hasattr(result, 'error') and result.error:
                error_msg = f"Supabase error in {operation_name}: {result.error.message}"
                logger.error(error_msg)
                raise SupabaseError(
                    message=result.error.message,
                    operation=operation_name,
                    original_error=result.error
                )
                
            return result
            
        except Exception as e:
            # Handle non-Supabase exceptions
            if not isinstance(e, SupabaseError):
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise SupabaseError(
                    message=str(e),
                    operation=func.__name__,
                    original_error=e
                )
            raise
    
    return wrapper


def safe_supabase_get(db: Client, table: str, id_value: Any, id_field: str = "id") -> Dict[str, Any]:
    """
    Safely retrieve a single record by ID with robust error handling.
    
    Args:
        db: Supabase client
        table: Table name to query
        id_value: Value of ID to search for
        id_field: Name of ID field (defaults to "id")
    
    Returns:
        Dict containing the record if found
        
    Raises:
        SupabaseError: If record not found or other error occurs
    """
    try:
        response = db.table(table).select("*").eq(id_field, id_value).execute()
        
        if not response.data or len(response.data) == 0:
            raise SupabaseError(
                message=f"Record not found in table '{table}' with {id_field}={id_value}",
                operation="get",
                table=table,
                data={"id_field": id_field, "id_value": id_value}
            )
            
        return response.data[0]
        
    except Exception as e:
        if not isinstance(e, SupabaseError):
            logger.error(f"Error retrieving record from {table}: {str(e)}")
            raise SupabaseError(
                message=str(e),
                operation="get",
                table=table,
                data={"id_field": id_field, "id_value": id_value},
                original_error=e
            )
        raise


def safe_supabase_insert(db: Client, table: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Safely insert record(s) with robust error handling.
    
    Args:
        db: Supabase client
        table: Table name
        data: Dict or List of dicts to insert
    
    Returns:
        Dict containing the inserted record(s)
        
    Raises:
        SupabaseError: If insert fails
    """
    try:
        response = db.table(table).insert(data).execute()
        
        if hasattr(response, 'error') and response.error:
            raise SupabaseError(
                message=response.error.message,
                operation="insert",
                table=table,
                data=data,
                original_error=response.error
            )
            
        return response.data
        
    except Exception as e:
        if not isinstance(e, SupabaseError):
            logger.error(f"Error inserting into {table}: {str(e)}")
            raise SupabaseError(
                message=str(e),
                operation="insert",
                table=table,
                data=data,
                original_error=e
            )
        raise


def safe_supabase_update(db: Client, table: str, data: Dict[str, Any], id_value: Any, id_field: str = "id") -> Dict[str, Any]:
    """
    Safely update a record with robust error handling.
    
    Args:
        db: Supabase client
        table: Table name
        data: Dict with update data
        id_value: Value of ID to update
        id_field: Name of ID field (defaults to "id")
    
    Returns:
        Dict containing the updated record
        
    Raises:
        SupabaseError: If update fails
    """
    try:
        response = db.table(table).update(data).eq(id_field, id_value).execute()
        
        if hasattr(response, 'error') and response.error:
            raise SupabaseError(
                message=response.error.message,
                operation="update",
                table=table,
                data={"id_field": id_field, "id_value": id_value, "update_data": data},
                original_error=response.error
            )
            
        if not response.data or len(response.data) == 0:
            raise SupabaseError(
                message=f"No record updated in table '{table}' with {id_field}={id_value}",
                operation="update",
                table=table,
                data={"id_field": id_field, "id_value": id_value, "update_data": data}
            )
            
        return response.data[0]
        
    except Exception as e:
        if not isinstance(e, SupabaseError):
            logger.error(f"Error updating record in {table}: {str(e)}")
            raise SupabaseError(
                message=str(e),
                operation="update",
                table=table,
                data={"id_field": id_field, "id_value": id_value, "update_data": data},
                original_error=e
            )
        raise