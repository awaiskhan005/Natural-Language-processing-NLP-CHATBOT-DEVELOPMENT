"""
SOLIDWORKS VBA ML API - Main Application
FastAPI server for training, testing, and generating VBA code
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys
from datetime import datetime

from api.routes import training, generation, validation, evaluation
from api.models import HealthResponse
from utils.logger import setup_logger
from config.settings import settings

# Setup logging
setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting SOLIDWORKS VBA ML API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.API_VERSION}")

    # Initialize model cache on startup
    try:
        from utils.model_cache import ModelCache
        model_cache = ModelCache()
        logger.info("✅ Model cache initialized")
    except Exception as e:
        logger.warning(f"⚠️ Model cache initialization failed: {e}")

    yield

    logger.info("👋 Shutting down SOLIDWORKS VBA ML API")

# Initialize FastAPI app
app = FastAPI(
    title="SOLIDWORKS VBA ML API",
    description="API for training and generating SOLIDWORKS VBA automation code using ML models",
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(training.router, prefix="/api/v1/training", tags=["Training"])
app.include_router(generation.router, prefix="/api/v1/generate", tags=["Code Generation"])
app.include_router(validation.router, prefix="/api/v1/validate", tags=["Validation"])
app.include_router(evaluation.router, prefix="/api/v1/evaluate", tags=["Evaluation"])


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return HealthResponse(
        status="healthy",
        message="SOLIDWORKS VBA ML API is running",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        message="API is operational",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
