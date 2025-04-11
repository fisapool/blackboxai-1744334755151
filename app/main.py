from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import logging.handlers
import uvicorn
from typing import List
import os
from datetime import datetime
import structlog
from uuid import uuid4

from app.core.settings import get_settings
from app.middleware.rate_limiter import rate_limit_middleware

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
    ]
)
logger = structlog.get_logger(__name__)

# Store app state
class AppState:
    def __init__(self):
        self.integrations = []
        self.startup_time = None
        self.health_checks = {}

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("starting_application", env=settings.APP_ENV)
    try:
        # Initialize integrations here
        from .integrations.multimodal import MultimodalIntegration
        integration = MultimodalIntegration()
        app_state.integrations.append(integration)
        await integration.start()
        
        # Record startup time
        app_state.startup_time = datetime.utcnow()
        
        # Initialize health checks
        app_state.health_checks = {
            "database": True,
            "redis": True,
            "integrations": True
        }
        
    except Exception as e:
        logger.error("startup_error", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("shutting_down_application")
    try:
        for integration in app_state.integrations:
            await integration.stop()
    except Exception as e:
        logger.error("shutdown_error", error=str(e), exc_info=True)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description="HR-focused multimodal analytics platform",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    # Bind request ID to logger context
    logger = structlog.get_logger().bind(request_id=request_id)
    
    # Add request ID to request state
    request.state.request_id = request_id
    request.state.logger = logger
    
    # Process request
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.error("request_failed", error=str(e), exc_info=True)
        raise

# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request.state.logger.error("http_error", 
        status_code=exc.status_code,
        detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request.state.request_id
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request.state.logger.error("unhandled_exception",
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": request.state.request_id
        },
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    uptime = datetime.utcnow() - app_state.startup_time
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "uptime_seconds": uptime.total_seconds(),
        "health_checks": app_state.health_checks
    }

# API routes
@app.get("/")
async def root():
    return {
        "message": "Welcome to HR Analytics Dashboard API",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs"
    }

# Import and include other routers
from .routers import analytics, users, monitoring
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4
    )
