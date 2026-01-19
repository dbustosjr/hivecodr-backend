"""HiveCodr Backend - FastAPI application with Supabase auth and CrewAI agents."""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.models.schemas import HealthResponse
from app.api.generate import router as generate_router
from app.api.generations import router as generations_router


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="HiveCodr Backend - AI-powered code generation with Developer Bee agents",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [
        "https://hivecodr.com",
        "https://app.hivecodr.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the health status of the API (no authentication required)"
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse: API health status
    """
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )


# Include API routers
app.include_router(
    generate_router,
    prefix=settings.API_V1_PREFIX,
    tags=["Generation"]
)

app.include_router(
    generations_router,
    prefix=settings.API_V1_PREFIX,
    tags=["Generations"]
)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    print(f"Claude Model: {settings.CLAUDE_MODEL}")
    print(f"Rate Limit: {settings.RATE_LIMIT_GENERATIONS} generations per {settings.RATE_LIMIT_WINDOW}s")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print("Shutting down HiveCodr Backend")


# This should ONLY be used for local development
# In production (Railway), Dockerfile CMD is used
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload for local development
    )
