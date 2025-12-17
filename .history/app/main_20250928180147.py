from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.database import create_tables, check_db_connection
from app.api import tourists, locations, alerts, ai_assessment, efir, frontend, realtime
from app.services.seed_data import seed_database
from app.logging import setup_logging

# Get logger 
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Smart Tourist Safety API...")
    
    # Check database connection
    if not await check_db_connection():
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")
    
    # Create tables
    await create_tables()
    
    # Initialize AI services for real-time processing
    logger.info("Initializing AI services...")
    try:
        from app.services.ai_engine import AIEngineService
        from app.api.ai_assessment import set_ai_engine
        
        ai_service = AIEngineService()
        await ai_service.initialize()
        
        # Set global AI engine for API endpoints
        set_ai_engine(ai_service)
        
        logger.info("AI services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing AI services: {e}")
        # Don't fail startup if AI services fail - they can be initialized later
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Smart Tourist Safety API...")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup enhanced logging
setup_logging(app)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Advanced logging is handled by the RequestLoggingMiddleware in app.logging


# Include API routers with /api/v1 prefix for new endpoints
app.include_router(tourists.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")  
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(ai_assessment.router, prefix="/api/v1")
app.include_router(efir.router, prefix="/api/v1")
app.include_router(frontend.router, prefix="/api/v1")
app.include_router(realtime.router, prefix="/api/v1")

# ✅ Include required endpoints without prefix for backward compatibility
app.include_router(tourists.router)  # Provides /registerTourist
app.include_router(locations.router) # Provides /sendLocation  
app.include_router(alerts.router)    # Provides /pressSOS, /getAlerts
app.include_router(efir.router)      # Provides /fileEFIR


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    db_healthy = await check_db_connection()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "timestamp": time.time(),
        "version": settings.api_version,
        "database": "connected" if db_healthy else "disconnected"
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Smart Tourist Safety & Incident Response System API",
        "version": settings.api_version,
        "docs_url": "/docs",
        "health_url": "/health",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug,
        log_level="info"
    )