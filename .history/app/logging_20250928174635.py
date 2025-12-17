"""
Enhanced logging middleware and utilities for the Smart Tourist Safety API.
This module provides detailed logging for API requests, responses, and data changes.
"""

import logging
import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any, Optional
import sys
import os
from datetime import datetime

# Configure logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Set up file handler for general logs
file_handler = logging.FileHandler("logs/api.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(log_format, date_format))

# Set up file handler for data change logs
change_file_handler = logging.FileHandler("logs/data_changes.log", encoding="utf-8")
change_file_handler.setFormatter(logging.Formatter(log_format, date_format))

# Set up console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(log_format, date_format))

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Create a separate logger for data changes
change_logger = logging.getLogger("data_changes")
change_logger.setLevel(logging.INFO)
change_logger.addHandler(change_file_handler)
change_logger.addHandler(console_handler)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses with detailed information.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate a unique request ID
        request_id = f"{time.time()}-{hash(request.client.host) % 10000}"
        
        # Extract request details
        path = request.url.path
        method = request.method
        query_params = dict(request.query_params)
        client_host = request.client.host
        client_port = request.client.port
        
        # Log request start
        logging.info(f"[{request_id}] Request started: {method} {path}")
        
        # Log request details at debug level
        logging.debug(
            f"[{request_id}] Request details: "
            f"Client: {client_host}:{client_port}, "
            f"Query params: {query_params}"
        )
        
        # Try to log request body for POST/PUT/PATCH requests
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # We need to read the body but also make it available again
                body = await request.body()
                # Decode and log the body content
                try:
                    body_json = json.loads(body)
                    logging.info(f"[{request_id}] Request body: {json.dumps(body_json)}")
                    # Add the request to the state for later use
                    request.state.body_json = body_json
                except json.JSONDecodeError:
                    logging.debug(f"[{request_id}] Request body is not JSON")
                
                # We need to create a new request with the same body for call_next
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
            except Exception as e:
                logging.error(f"[{request_id}] Error reading request body: {e}")
        
        # Record start time to measure duration
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response
            logging.info(
                f"[{request_id}] Response: {response.status_code} "
                f"(took {duration:.4f}s)"
            )
            
            # Add request ID to response headers for tracking
            response.headers["X-Request-ID"] = request_id
            
            # Special handling for data modification endpoints
            if method in ["POST", "PUT", "PATCH", "DELETE"] and response.status_code < 400:
                await self.log_data_change(request, response, request_id)
            
            return response
        except Exception as e:
            # Log any unhandled exceptions
            duration = time.time() - start_time
            logging.error(
                f"[{request_id}] Unhandled exception: {str(e)} "
                f"(took {duration:.4f}s)"
            )
            raise
    
    async def log_data_change(self, request: Request, response: Response, request_id: str):
        """Log detailed information about data changes."""
        path = request.url.path
        method = request.method
        
        # Determine the entity type being modified based on URL path
        entity_type = self.extract_entity_type(path)
        entity_id = self.extract_entity_id(path)
        
        # Describe the operation
        operation = self.describe_operation(method)
        
        # Get request body if available
        body_data = getattr(request.state, "body_json", None)
        
        # Log the data change
        change_logger.info(
            f"[{request_id}] {operation} {entity_type}"
            f"{f' (ID: {entity_id})' if entity_id else ''}"
        )
        
        if body_data:
            # Mask sensitive data before logging
            masked_data = self.mask_sensitive_data(body_data)
            change_logger.info(
                f"[{request_id}] Data: {json.dumps(masked_data)}"
            )
    
    def extract_entity_type(self, path: str) -> str:
        """Extract entity type from URL path."""
        # Strip /api/v1 prefix if present
        path = path.replace("/api/v1", "")
        
        # Map paths to entity types
        if "/tourists" in path:
            return "Tourist"
        elif "/locations" in path:
            return "Location"
        elif "/alerts" in path or "/pressSOS" in path:
            return "Alert"
        elif "/getRestrictedZones" in path or "/safe-zones" in path:
            return "Zone"
        elif "/fileEFIR" in path:
            return "E-FIR"
        else:
            return "Unknown Entity"
    
    def extract_entity_id(self, path: str) -> Optional[str]:
        """Extract entity ID from URL path if present."""
        parts = path.split("/")
        for i, part in enumerate(parts):
            if i > 0 and parts[i-1] in ["tourists", "locations", "alerts"] and part.isdigit():
                return part
        return None
    
    def describe_operation(self, method: str) -> str:
        """Convert HTTP method to operation description."""
        operations = {
            "POST": "Created",
            "PUT": "Updated",
            "PATCH": "Partially updated",
            "DELETE": "Deleted"
        }
        return operations.get(method, "Modified")
    
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in data before logging."""
        if not isinstance(data, dict):
            return data
            
        # Create a deep copy to avoid modifying the original
        masked = data.copy()
        
        # List of sensitive fields to mask
        sensitive_fields = [
            "password", "token", "secret", "key", "passport_number",
            "emergency_contact", "contact", "email"
        ]
        
        for field in sensitive_fields:
            if field in masked:
                if isinstance(masked[field], str) and len(masked[field]) > 4:
                    # Show only first and last character
                    masked[field] = f"{masked[field][0]}****{masked[field][-1]}"
                else:
                    masked[field] = "****"
        
        # Recursively mask nested dictionaries
        for key, value in masked.items():
            if isinstance(value, dict):
                masked[key] = self.mask_sensitive_data(value)
        
        return masked


# Helper function to log specific events
def log_event(event_type: str, description: str, data: Any = None, level: int = logging.INFO):
    """Log a specific event with structured information."""
    if data and isinstance(data, dict):
        # Mask sensitive data
        middleware = APILoggingMiddleware(None)
        data = middleware.mask_sensitive_data(data)
    
    message = f"EVENT: {event_type} - {description}"
    if data:
        try:
            if isinstance(data, dict):
                message += f" - Data: {json.dumps(data)}"
            else:
                message += f" - Data: {str(data)}"
        except:
            message += f" - Data: [Could not serialize]"
    
    logging.log(level, message)


# Function to log when a Tourist enters a restricted zone
def log_geofence_event(tourist_id: int, zone_name: str, latitude: float, longitude: float):
    """Log when a tourist enters a restricted zone."""
    change_logger.warning(
        f"⚠️ GEOFENCE ALERT - Tourist {tourist_id} entered restricted zone '{zone_name}' "
        f"at coordinates ({latitude}, {longitude})"
    )


# Function to log SOS events
def log_sos_event(tourist_id: int, message: str, latitude: float, longitude: float):
    """Log when a tourist sends an SOS signal."""
    change_logger.critical(
        f"🆘 SOS ALERT - Tourist {tourist_id} sent emergency signal "
        f"at coordinates ({latitude}, {longitude}): {message}"
    )


# Function to log AI safety assessments
def log_safety_assessment(tourist_id: int, safety_score: int, severity: str, factors: Dict):
    """Log AI safety assessment for a tourist."""
    change_logger.info(
        f"🤖 SAFETY ASSESSMENT - Tourist {tourist_id} - "
        f"Score: {safety_score} - Severity: {severity} - "
        f"Factors: {json.dumps(factors)}"
    )


# Function to log application startup and shutdown events
def log_application_event(event_type: str, details: str = None):
    """Log application lifecycle events."""
    if event_type == "startup":
        logging.info(f"🚀 APPLICATION STARTING - Smart Tourist Safety API - {datetime.now().isoformat()}")
        if details:
            logging.info(f"Startup details: {details}")
    elif event_type == "shutdown":
        logging.info(f"🛑 APPLICATION STOPPING - Smart Tourist Safety API - {datetime.now().isoformat()}")
        if details:
            logging.info(f"Shutdown details: {details}")
    else:
        logging.info(f"APPLICATION EVENT: {event_type} - {details or ''}")