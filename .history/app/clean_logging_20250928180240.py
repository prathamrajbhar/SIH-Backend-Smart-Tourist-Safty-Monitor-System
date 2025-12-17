"""
Clean and concise logging system for API request/response tracking
"""
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, List, Set
import uuid
import os

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure the loggers with clean formatting
# For console: simplified colored output
# For file: more detailed structured data

# Define a clean, colorful formatter for console output
class ColoredFormatter(logging.Formatter):
    """
    Formatter that adds colors to logs in console
    """
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',   # Red
        'CRITICAL': '\033[41m\033[37m',  # White on Red
        'RESET': '\033[0m'    # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        return log_message

# Create console handler with colored formatting
console_handler = logging.StreamHandler(sys.stdout)
console_format = '%(asctime)s | %(levelname)-7s | %(message)s'
colored_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')
console_handler.setFormatter(colored_formatter)

# Create file handler with more detailed but clean formatting
file_handler = logging.FileHandler("logs/api.log")
file_format = '%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s'
file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.handlers = []  # Remove any existing handlers
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO)

# Create specific loggers
api_logger = logging.getLogger("api")
access_logger = logging.getLogger("access")
error_logger = logging.getLogger("error")

# Quiet down noisy loggers
for logger_name in ['uvicorn', 'uvicorn.error', 'httpx']:
    noisy_logger = logging.getLogger(logger_name)
    if logger_name == 'httpx':
        noisy_logger.setLevel(logging.WARNING)  # Only warnings and above for httpx
    else:
        noisy_logger.setLevel(logging.INFO)


class CleanRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for clean logging of API requests and responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Paths that don't need to be logged
        self.exclude_paths: Set[str] = {
            '/health', '/metrics', '/favicon.ico', 
            '/docs', '/redoc', '/openapi.json', 
            '/static/'
        }
        # Specific paths to log even if they would normally be excluded
        self.always_log_paths: Set[str] = {
            '/registerTourist', '/sendLocation', '/pressSOS'
        }
    
    def should_log_path(self, path: str) -> bool:
        """Determine if this path should be logged based on rules"""
        # Always log specific important paths
        if any(path.startswith(important) for important in self.always_log_paths):
            return True
            
        # Skip excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return False
            
        # Log all other paths
        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for excluded paths
        should_log = self.should_log_path(request.url.path)
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]  # Shorter ID for cleaner logs
        request.state.request_id = request_id
        start_time = time.time()
        
        # Extract basic request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Log the request (only if it should be logged)
        if should_log:
            access_logger.info(f"→ {request_id} | {method} {path} | Client: {client_ip}")
        
        # Process the request and catch any errors
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Prepare log message based on status code
            status_code = response.status_code
            
            # Log the response (only if request was logged)
            if should_log:
                # Use different log levels based on status code
                if status_code >= 500:
                    access_logger.error(
                        f"← {request_id} | {status_code} | {method} {path} | {process_time*1000:.0f}ms")
                elif status_code >= 400:
                    access_logger.warning(
                        f"← {request_id} | {status_code} | {method} {path} | {process_time*1000:.0f}ms")
                else:
                    access_logger.info(
                        f"← {request_id} | {status_code} | {method} {path} | {process_time*1000:.0f}ms")
            
            # Add request ID to response headers for tracking
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            # Always log exceptions regardless of path
            error_time = time.time() - start_time
            error_logger.exception(
                f"! {request_id} | Error processing {method} {path} after {error_time*1000:.0f}ms: {str(e)}")
            raise


def setup_clean_logging(app: FastAPI) -> None:
    """Setup clean, focused logging for the FastAPI application"""
    
    # Add request/response logging middleware
    app.add_middleware(CleanRequestLoggingMiddleware)
    
    # Log application startup with clean format
    api_logger.info(f"🚀 Starting {app.title} v{app.version}")
    api_logger.info(f"Environment: {app.debug}")
    
    # Return the root logger for additional configuration if needed
    return root_logger