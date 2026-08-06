"""FastAPI application entry point"""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.config import settings
from app.api import auth, events, personas, recommendations, admin, products

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"] if settings.rate_limit_enabled else [],
    storage_uri=settings.redis_url if settings.rate_limit_enabled else "memory://"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic"""
    # --- Startup ---
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")

    if settings.scheduler_enabled:
        from app.scheduler import start_scheduler
        start_scheduler()
        logger.info("APScheduler started")

    logger.info("Application startup complete")
    yield  # Application runs here

    # --- Shutdown ---
    logger.info("Shutting down application")

    if settings.scheduler_enabled:
        from app.scheduler import shutdown_scheduler
        shutdown_scheduler()
        logger.info("APScheduler stopped")

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Behavioral AI Recommendation Platform for online learning marketplaces",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug,
    lifespan=lifespan,
)

# Register rate limiter with app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for React frontend
# Production: Use specific origins from settings, not wildcard
allowed_origins = settings.cors_origins if settings.is_production else [
    "http://localhost:3000",  # React dev server (Create React App)
    "http://localhost:5173",  # Vite dev server
    *settings.cors_origins      # Additional origins from config
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(events.router, tags=["Events"])
app.include_router(personas.router, tags=["Personas"])
app.include_router(recommendations.router, tags=["Recommendations"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(products.router, tags=["Products"])



# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions and return JSON with trace_id"""
    trace_id = str(uuid.uuid4())
    logger.warning(
        f"HTTP {exc.status_code} - {exc.detail} | "
        f"path={request.url.path} | trace_id={trace_id}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "trace_id": trace_id
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return 422 JSON with trace_id"""
    trace_id = str(uuid.uuid4())
    logger.warning(
        f"Validation error | path={request.url.path} | "
        f"errors={exc.errors()} | trace_id={trace_id}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "trace_id": trace_id
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with trace_id logging (no stack trace exposed)"""
    trace_id = str(uuid.uuid4())
    
    # Log the actual error for debugging (with stack trace)
    logger.error(
        f"Unhandled exception | path={request.url.path} | "
        f"trace_id={trace_id} | error={str(exc)}",
        exc_info=True
    )
    
    # Return generic message to client (never expose stack trace or internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "trace_id": trace_id
        }
    )



@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.app_env,
        "docs": "/docs",
        "api": {
            "auth": {
                "register": "/auth/register",
                "login": "/auth/login",
                "me": "/auth/me",
                "refresh": "/auth/refresh"
            }
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    return {"status": "ok", "version": "1.0.0"}



@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for Prometheus
    """
    if not settings.enable_metrics:
        return JSONResponse(
            content={"error": "Metrics are disabled"},
            status_code=404
        )
    
    # TODO: Implement Prometheus metrics
    return {
        "message": "Metrics endpoint - implementation pending"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
