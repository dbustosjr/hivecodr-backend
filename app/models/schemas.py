"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import bleach


class GenerateRequest(BaseModel):
    """Request model for code generation."""

    requirements: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Plain English requirements for code generation"
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


class GenerateResponse(BaseModel):
    """Response model for code generation."""

    id: str = Field(..., description="Generation ID")
    code: Dict[str, Any] = Field(..., description="Generated code files")
    agent_log: str = Field(..., description="Agent execution log")
    created_at: datetime = Field(..., description="Generation timestamp")


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
