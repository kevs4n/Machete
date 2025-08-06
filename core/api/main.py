"""
MACHETE Platform - Python FastAPI Backend
Main application entry point with FastAPI configuration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.health import router as health_router
from app.api.tools import router as tools_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🔪 MACHETE Platform starting up...")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    yield
    # Shutdown
    logger.info("🔪 MACHETE Platform shutting down...")

# Create FastAPI application
app = FastAPI(
    title="MACHETE Platform API",
    description="Multi-purpose Automation & Configuration Hub for Engineering Tools and Execution",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"HTTP {request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers
app.include_router(health_router, prefix="/api")
app.include_router(tools_router, prefix="/api")

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with platform information"""
    return {
        "name": "MACHETE Platform API",
        "version": "2.0.0",
        "description": "Multi-purpose Automation & Configuration Hub for Engineering Tools and Execution",
        "docs_url": "/api/docs",
        "health_check": "/api/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=False  # We handle logging in middleware
    )
