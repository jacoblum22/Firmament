from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from datetime import datetime
from routes import router
from config import settings
from middleware import SecurityHeadersMiddleware, RateLimitMiddleware
import logging
from pathlib import Path

# Configure logging
log_file = None
if settings.log_file:
    # Create log directory if it doesn't exist
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = settings.log_file

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=log_file,
)
logger = logging.getLogger(__name__)

# Create FastAPI app with environment-specific settings
app = FastAPI(
    title="StudyMate API",
    description="StudyMate v2 backend API for audio processing and study material generation",
    version="2.0.0",
    debug=settings.debug,
    # Hide docs in production unless explicitly enabled
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Log startup information
logger.info(f"Starting StudyMate API in {settings.environment} mode")
logger.info(f"Debug mode: {settings.debug}")
logger.info(f"CORS origins: {settings.allowed_origins}")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control",
        "Pragma",
    ],
    expose_headers=["*"],
    max_age=settings.cors_max_age,
)

# Production-specific middleware
if settings.is_production:
    logger.info("Applying production middleware")

    # Add trusted host middleware for production
    if settings.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts,
        )
        logger.info(f"Trusted hosts configured: {settings.trusted_hosts}")

    # Add security headers middleware
    if settings.secure_headers:
        app.add_middleware(SecurityHeadersMiddleware)
        logger.info("Security headers middleware enabled")

    # Add rate limiting middleware with production settings
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.rate_limit_calls,
        period=settings.rate_limit_period,
    )
    logger.info(
        f"Rate limiting: {settings.rate_limit_calls} calls per {settings.rate_limit_period} seconds"
    )

# Development-specific middleware
elif settings.is_development:
    logger.info("Running in development mode")

    # Add rate limiting middleware with development settings (more lenient)
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.rate_limit_calls,
        period=settings.rate_limit_period,
    )
    logger.info(
        f"Development rate limiting: {settings.rate_limit_calls} calls per {settings.rate_limit_period} seconds"
    )

app.include_router(router)


@app.get("/")
def read_root():
    return {
        "message": "StudyMate v2 backend is live!",
        "environment": settings.environment,
        "version": "2.0.0",
        "debug": settings.debug,
        "cors_origins": settings.allowed_origins if settings.debug else "configured",
        "docs_url": "/docs" if settings.debug else "disabled",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "debug": settings.debug,
        "version": "2.0.0",
    }


@app.get("/config")
def get_config():
    """Get current configuration (debug info only available in development)"""
    base_config = {
        "environment": settings.environment,
        "version": "2.0.0",
        "debug": settings.debug,
    }

    # Only expose detailed config in development
    if settings.is_development:
        base_config.update(
            {
                "cors_origins": settings.allowed_origins,
                "host": settings.host,
                "port": settings.port,
                "reload": settings.reload,
                "log_level": settings.log_level,
                "rate_limit": {
                    "calls": settings.rate_limit_calls,
                    "period": settings.rate_limit_period,
                },
                "upload_settings": {
                    "max_size": settings.upload_max_size,
                    "directory": settings.upload_directory,
                    "temp_directory": settings.temp_directory,
                },
            }
        )

    return base_config
