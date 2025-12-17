"""
Enhanced logging system for API request/response tracking
"""
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # Log to console
        logging.StreamHandler(sys.stdout),
        # Log to file with rotation
        logging.FileHandler("logs/api.log"),
    ]
)

# Create loggers
api_logger = logging.getLogger("api")
access_logger = logging.getLogger("access")
error_logger = logging.getLogger("error")
security_logger = logging.getLogger("security")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed logging of API requests and responses.
    """

    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        # Prepare request data
        request_data = await self._get_request_data(request)
        log_data = {
            "request_id": request_id,
            "client_ip": request.client.host if request.client else None,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "timestamp": datetime.now().isoformat(),
            "user_agent": request.headers.get("user-agent"),
            "request_data": request_data,
        }

        # Log the request
        access_logger.info(f"API Request: {json.dumps(log_data)}")

        # Process the request and catch any errors
        try:
            # Create a response with our custom response logger
            start_time = time.time()
            
            # Call the next middleware/endpoint handler
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response information
            response_log = {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "content_type": response.headers.get("content-type"),
                "timestamp": datetime.now().isoformat(),
            }
            
            # Log based on status code
            if 200 <= response.status_code < 400:
                access_logger.info(f"API Response: {json.dumps(response_log)}")
            elif 400 <= response.status_code < 500:
                access_logger.warning(f"API Client Error: {json.dumps(response_log)}")
            else:
                access_logger.error(f"API Server Error: {json.dumps(response_log)}")
                
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log exceptions during request handling
            error_log = {
                "request_id": request_id,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.now().isoformat(),
            }
            error_logger.exception(f"API Exception: {json.dumps(error_log)}")
            
            # Re-raise the exception for FastAPI's exception handlers
            raise

    async def _get_request_data(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract request data safely from various request types"""
        try:
            # Try to extract JSON body for JSON requests
            if "application/json" in request.headers.get("content-type", ""):
                body = await request.body()
                if body:
                    # Redact sensitive fields if needed
                    data = json.loads(body)
                    # Redact sensitive information like passwords
                    if isinstance(data, dict):
                        if "password" in data:
                            data["password"] = "********"
                        if "token" in data:
                            data["token"] = "********"
                    return data
                
            # For form data, just log that it was received but not the actual data
            elif "form" in request.headers.get("content-type", ""):
                return {"form_data": "Received but not logged for privacy"}
                
            # Default for other content types
            return None
        except Exception as e:
            access_logger.warning(f"Failed to extract request data: {e}")
            return None


def setup_logging(app: FastAPI) -> None:
    """Setup enhanced logging for the FastAPI application"""
    
    # Add request/response logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Log application startup
    api_logger.info(
        f"🚀 APPLICATION STARTING - {app.title} - "
        f"{datetime.now().isoformat()}"
    )
    
    api_logger.info(f"Startup details: Environment: {app.debug}")