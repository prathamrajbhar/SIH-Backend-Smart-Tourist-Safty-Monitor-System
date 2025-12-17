from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings
from app.database import create_tables, check_db_connection

# Import all Supabase-based API modules
import app.api.tourists_supabase as tourists
import app.api.locations_supabase as locations
import app.api.alerts_supabase as alerts
import app.api.efir_supabase as efir
import app.api.zones_supabase as zones
import app.api.safety_supabase as safety
from app.api import frontend, realtime  # Keep original if not yet migrated

from app.services.seed_data import seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
        from app.services.ai_engine_supabase import AIEngineService
        
        ai_service = AIEngineService()
        await ai_service.initialize()
        
        # We're using simpler AI models directly in the API modules
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

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response


# Include API routers with /api/v1 prefix for new endpoints
app.include_router(tourists.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")  
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(safety.router, prefix="/api/v1")
app.include_router(efir.router, prefix="/api/v1")
app.include_router(zones.router, prefix="/api/v1")
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