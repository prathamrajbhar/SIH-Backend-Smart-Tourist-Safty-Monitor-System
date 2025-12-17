#!/usr/bin/env python3
"""
Smart Tourist Safety & Incident Response System
Run script with enhanced logging setup
"""
import os
import sys
import logging
import uvicorn
import argparse
from pathlib import Path

# Setup script directory
script_dir = Path(__file__).parent.absolute()
sys.path.append(str(script_dir))

# Import our logging setup
from app.logging import log_application_event

# Parse command line arguments
parser = argparse.ArgumentParser(description="Run the Smart Tourist Safety API with enhanced logging")
parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
parser.add_argument("--log-level", default="info", help="Logging level (debug, info, warning, error, critical)")
args = parser.parse_args()

# Ensure logs directory exists
logs_dir = os.path.join(script_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Run the application with enhanced logging
if __name__ == "__main__":
    # Log startup
    log_application_event(
        "startup",
        f"Starting server on {args.host}:{args.port} with log level {args.log_level}"
    )
    
    # Run uvicorn
    uvicorn.run(
        "app.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level=args.log_level
    )