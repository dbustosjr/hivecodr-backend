"""Rate limiting for API endpoints."""

from datetime import datetime, timedelta
from fastapi import HTTPException, status
from supabase import Client
from app.core.config import settings
from app.core.auth import CurrentUser


async def check_rate_limit(user: CurrentUser, supabase: Client) -> None:
    """
    Checks if user has exceeded their rate limit for generations.

    Args:
        user: Current authenticated user
        supabase: Supabase client instance

    Raises:
        HTTPException: If user has exceeded rate limit
    """
    try:
        # Fetch user usage from database
        response = supabase.table("user_usage").select("*").eq("user_id", user.user_id).execute()

        current_time = datetime.utcnow()

        if not response.data or len(response.data) == 0:
            # First time user - create usage record
            supabase.table("user_usage").insert({
                "user_id": user.user_id,
                "generation_count": 0,
                "last_reset": current_time.isoformat()
            }).execute()
            return

        user_usage = response.data[0]
        generation_count = user_usage.get("generation_count", 0)
        last_reset = datetime.fromisoformat(user_usage.get("last_reset").replace("Z", "+00:00"))

        # Check if rate limit window has passed
        time_since_reset = (current_time - last_reset).total_seconds()

        if time_since_reset >= settings.RATE_LIMIT_WINDOW:
            # Reset counter
            supabase.table("user_usage").update({
                "generation_count": 0,
                "last_reset": current_time.isoformat()
            }).eq("user_id", user.user_id).execute()
            return

        # Check if user exceeded rate limit
        if generation_count >= settings.RATE_LIMIT_GENERATIONS:
            time_remaining = settings.RATE_LIMIT_WINDOW - time_since_reset
            minutes_remaining = int(time_remaining / 60)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. You can make {settings.RATE_LIMIT_GENERATIONS} generations per hour. Try again in {minutes_remaining} minutes."
            )

    except HTTPException:
        raise
    except Exception as e:
        # Log error but don't block request
        print(f"Rate limit check error: {str(e)}")


async def increment_usage(user: CurrentUser, supabase: Client) -> None:
    """
    Increments the user's generation count.

    Args:
        user: Current authenticated user
        supabase: Supabase client instance
    """
    try:
        # Increment generation count
        response = supabase.table("user_usage").select("generation_count").eq("user_id", user.user_id).execute()

        if response.data:
            current_count = response.data[0].get("generation_count", 0)
            supabase.table("user_usage").update({
                "generation_count": current_count + 1
            }).eq("user_id", user.user_id).execute()

    except Exception as e:
        # Log error but don't block request
        print(f"Usage increment error: {str(e)}")
