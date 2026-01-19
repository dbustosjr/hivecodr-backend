"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import bleach
import re


class GenerateRequest(BaseModel):
    """Request model for code generation."""

    requirements: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Plain English requirements for code generation"
    )

    deploy: bool = Field(
        default=False,
        description="Whether to automatically deploy to Railway and Vercel"
    )

    app_name: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Application name for deployment (required if deploy=true)"
    )

    @field_validator("requirements")
    @classmethod
    def sanitize_requirements(cls, v: str) -> str:
        """Sanitize input to prevent XSS and HTML injection."""
        # Strip all HTML tags and attributes
        cleaned = bleach.clean(v, tags=[], strip=True)
        # Remove extra whitespace
        cleaned = " ".join(cleaned.split())
        return cleaned

    @field_validator("app_name")
    @classmethod
    def validate_app_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate app_name is URL-safe."""
        if v is None:
            return v

        # Convert to lowercase and validate format
        v = v.lower().strip()

        # Check format: lowercase alphanumeric and hyphens only
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError(
                "app_name must contain only lowercase letters, numbers, and hyphens"
            )

        # Cannot start or end with hyphen
        if v.startswith('-') or v.endswith('-'):
            raise ValueError("app_name cannot start or end with a hyphen")

        # Cannot have consecutive hyphens
        if '--' in v:
            raise ValueError("app_name cannot contain consecutive hyphens")

        return v

    def model_post_init(self, __context):
        """Validate that app_name is provided when deploy=true."""
        if self.deploy and not self.app_name:
            raise ValueError("app_name is required when deploy=true")


class GenerateResponse(BaseModel):
    """Response model for code generation."""

    id: str = Field(..., description="Generation ID")
    code: Dict[str, Any] = Field(..., description="Generated code files")
    agent_log: str = Field(..., description="Agent execution log")
    created_at: datetime = Field(..., description="Generation timestamp")

    # Deployment information (optional)
    deployed: bool = Field(default=False, description="Whether the app was deployed")
    deployment_status: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Deployment status for backend and frontend"
    )
    backend_url: Optional[str] = Field(default=None, description="Live backend URL")
    frontend_url: Optional[str] = Field(default=None, description="Live frontend URL")
    deployment_time: Optional[str] = Field(
        default=None,
        description="Time taken for deployment"
    )
    deployment_configs_ready: bool = Field(
        default=False,
        description="Whether deployment configuration files were generated"
    )


class Generation(BaseModel):
    """Model for a stored generation."""

    id: str
    user_id: str
    requirements: str
    generated_code: Optional[Dict[str, Any]] = None
    agent_outputs: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerationListResponse(BaseModel):
    """Response model for list of generations."""

    generations: list[Generation]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    environment: str


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    code: Optional[str] = None
