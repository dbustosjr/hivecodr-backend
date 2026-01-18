"""API endpoint for retrieving past generations."""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.models.schemas import GenerationListResponse, Generation
from app.core.auth import get_current_user, get_supabase_client, CurrentUser


router = APIRouter()


@router.get(
    "/generations",
    response_model=GenerationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's past generations",
    description="Retrieves all code generations for the authenticated user"
)
async def get_generations(
    current_user: CurrentUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get all past generations for the authenticated user.

    Args:
        current_user: Authenticated user from JWT token
        supabase: Supabase client for database operations

    Returns:
        GenerationListResponse: List of user's generations

    Raises:
        HTTPException: If database query fails
    """
    try:
        # Query generations for current user (RLS policy handles filtering)
        response = supabase.table("generations") \
            .select("*") \
            .eq("user_id", current_user.user_id) \
            .order("created_at", desc=True) \
            .execute()

        if not response.data:
            return GenerationListResponse(generations=[], total=0)

        # Convert to Generation models
        generations = [
            Generation(
                id=gen["id"],
                user_id=gen["user_id"],
                requirements=gen["requirements"],
                generated_code=gen.get("generated_code"),
                agent_outputs=gen.get("agent_outputs"),
                created_at=gen["created_at"]
            )
            for gen in response.data
        ]

        return GenerationListResponse(
            generations=generations,
            total=len(generations)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve generations: {str(e)}"
        )
