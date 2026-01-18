"""Verify JWT authentication without triggering code generation."""

import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


def verify_token_manually(token: str):
    """Manually verify a token like the auth middleware does."""

    print(f"\n{'='*80}")
    print("Manual Token Verification (simulating auth middleware)")
    print(f"{'='*80}\n")

    print(f"Token (first 50 chars): {token[:50]}...")
    print(f"Token length: {len(token)}\n")

    try:
        # This is exactly what auth.py does
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        print("SUCCESS: Token is valid!")
        print("\nDecoded payload:")
        for key, value in payload.items():
            print(f"  {key}: {value}")

        # Extract user info like auth.py does
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            print("\nERROR: Token missing user ID (sub claim)")
            return False

        print(f"\nAuthenticated as:")
        print(f"  User ID: {user_id}")
        print(f"  Email: {email}")

        print(f"\n{'='*80}")
        print("Authentication would succeed in the API!")
        print(f"{'='*80}\n")

        return True

    except jwt.ExpiredSignatureError:
        print("ERROR: Token has expired")
        return False
    except jwt.InvalidTokenError as e:
        print(f"ERROR: Invalid token - {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__} - {str(e)}")
        return False


def main():
    """Generate a fresh token and verify it."""

    # Generate fresh token
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=24)

    user_id = "6fed75bd-3531-4fde-b657-8feca6dd50b1"
    email = "test@hivecodr.com"

    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp())
    }

    print(f"\n{'='*80}")
    print("Generating Fresh JWT Token")
    print(f"{'='*80}\n")

    token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")

    print(f"Token generated for: {email}")
    print(f"User ID: {user_id}")
    print(f"Expires: {datetime.fromtimestamp(payload['exp'], tz=timezone.utc)}")
    print(f"\nToken:\n{token}\n")

    # Verify it
    verify_token_manually(token)

    print("\nUse this token in API requests:")
    print(f"Authorization: Bearer {token}\n")


if __name__ == "__main__":
    main()
