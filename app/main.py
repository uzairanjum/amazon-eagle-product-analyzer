"""
AMZ Eagle Product Analyzer - Main Application
==============================================

FastAPI application entry point.

IMPROVEMENT OPPORTUNITIES:
1. Add middleware for logging
2. Add middleware for authentication
3. Add error handlers
4. Add health checks
5. Add rate limiting
6. Add request ID tracking
7. Add CORS configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import get_settings
from app.schemas.request import HealthResponse
from app.api.routes import analyze, asins, candidates

# Initialize FastAPI app
app = FastAPI(
    title="AMZ Eagle Product Analyzer",
    description="""
    Internal Amazon Operations Platform - Product Opportunity Decision Engine
    
    This module analyzes Amazon product opportunities by:
    - Fetching historical data from Keepa API
    - Normalizing time-series data
    - Scoring product opportunities
    - Generating 3-phase forecasts
    - Calculating economics and enforcing margin requirements
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware
# IMPROVEMENT: Configure allowed origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # IMPROVEMENT: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ROUTES
# ============================================================================

# Include routers
app.include_router(analyze.router)
app.include_router(asins.router)
app.include_router(candidates.router)


# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Application status
    """
    return HealthResponse(status="healthy", version="1.0.0")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": "AMZ Eagle Product Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ============================================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.

    IMPROVEMENTS:
    1. Initialize connection pool
    2. Load configuration
    3. Run database migrations
    """
    settings = get_settings()
    print(f"Starting AMZ Eagle Product Analyzer...")
    print(f"Environment: {settings.app_env}")
    print(f"Supabase: {settings.supabase_url}")
    print(f"Keepa Domain: {settings.keepa_domain}")
    print(f"Mock Mode: {settings.enable_mock_data}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.

    IMPROVEMENTS:
    1. Close connection pool
    2. Cancel pending tasks
    3. Save state
    """
    print("Shutting down AMZ Eagle Product Analyzer...")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

# IMPROVEMENT: Add custom error handlers
# from fastapi import Request, status
# from fastapi.responses import JSONResponse
#
# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     return JSONResponse(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         content={"error": "Internal server error", "detail": str(exc)}
#     )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
