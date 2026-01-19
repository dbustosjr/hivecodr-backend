"""HiveCodr Backend - FastAPI application with Supabase auth and CrewAI agents."""

# CRITICAL: Monkey-patch httpx BEFORE any imports to force HTTP/2 for Railway
import httpx
_original_httpx_client_init = httpx.Client.__init__
def _patched_httpx_client_init(self, **kwargs):
    """Force HTTP/2 for all httpx clients (Railway requirement)."""
    kwargs.setdefault('http2', True)
    kwargs.setdefault('timeout', 120.0)
    _original_httpx_client_init(self, **kwargs)
httpx.Client.__init__ = _patched_httpx_client_init

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
    docs_url="/docs",  # Always enable docs for now
    redoc_url="/redoc"  # Always enable redoc for now
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [
        "https://hivecodr-backend-production.up.railway.app",
        "https://hivecodr.com",
        "https://app.hivecodr.com",
        "https://*.vercel.app",  # Allow Vercel preview deployments
        "http://localhost:3000",  # Local frontend development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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


@app.get(
    "/debug/anthropic",
    tags=["Debug"],
    summary="Test Anthropic API connection",
    description="Debug endpoint to test ChatAnthropic initialization and API calls with HTTP/2"
)
async def debug_anthropic():
    """Debug endpoint to test Anthropic API with HTTP/2."""
    import os
    import httpx
    from anthropic import Anthropic

    result = {
        "api_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
        "model": settings.CLAUDE_MODEL,
        "http2_enabled": True,
        "test_status": "pending"
    }

    try:
        # Create HTTP client with HTTP/2 support
        http_client = httpx.Client(
            http2=True,
            timeout=120.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        # Initialize Anthropic client with HTTP/2
        client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            http_client=http_client,
            timeout=120.0,
            max_retries=3
        )
        result["initialization"] = "success"

        # Test API call
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=50,
            messages=[{"role": "user", "content": "Say hello"}]
        )
        result["test_status"] = "success"
        result["response"] = response.content[0].text
    except Exception as e:
        result["test_status"] = "failed"
        result["error"] = f"{type(e).__name__}: {str(e)}"

    return result


@app.get(
    "/debug/architect-bee",
    tags=["Debug"],
    summary="Test Architect Bee initialization",
    description="Debug endpoint to test Architect Bee ChatAnthropic with HTTP/2"
)
async def debug_architect_bee():
    """Debug endpoint to test Architect Bee initialization."""
    import os
    import httpx
    from langchain_anthropic import ChatAnthropic

    result = {
        "api_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
        "model": settings.CLAUDE_MODEL,
        "http2_enabled": True,
        "test_status": "pending"
    }

    try:
        # Create HTTP client with HTTP/2 support (same as Architect Bee)
        http_client = httpx.Client(
            http2=True,
            timeout=120.0,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )

        # Initialize ChatAnthropic with HTTP/2 (same as Architect Bee)
        model = ChatAnthropic(
            model=settings.CLAUDE_MODEL,
            temperature=0.7,
            max_tokens=100,
            timeout=120.0,
            max_retries=3
        )

        # Workaround: Manually assign HTTP/2 client to internal Anthropic client
        # See: https://github.com/langchain-ai/langchain/issues/30146
        model._client._client = http_client
        result["initialization"] = "success"

        # Test API call
        response = model.invoke("Say hello in one sentence")
        result["test_status"] = "success"
        result["response"] = str(response.content)
    except Exception as e:
        result["test_status"] = "failed"
        result["error"] = f"{type(e).__name__}: {str(e)}"
        import traceback
        result["traceback"] = traceback.format_exc()

    return result


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
