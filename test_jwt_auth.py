"""Test JWT token generation and validation."""

import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def test_jwt_round_trip():
    """Test generating and decoding a JWT token."""

    print(f"\n{'='*80}")
    print("JWT Authentication Test")
    print(f"{'='*80}\n")

    # Print the secret (first few chars only for security)
    print(f"JWT Secret (first 10 chars): {SUPABASE_JWT_SECRET[:10]}...")
    print(f"JWT Secret length: {len(SUPABASE_JWT_SECRET)}")
    print(f"JWT Secret type: {type(SUPABASE_JWT_SECRET)}\n")

    # Generate token
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

    print("Step 1: Generating token...")
    token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
    print(f"Token generated successfully!")
    print(f"Token type: {type(token)}")
    print(f"Token: {token}\n")

    # Decode token
    print("Step 2: Decoding token...")
    try:
        decoded = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        print(f"Token decoded successfully!")
        print(f"Decoded payload:")
        for key, value in decoded.items():
            print(f"  {key}: {value}")

        print(f"\n{'='*80}")
        print("SUCCESS: Token generation and validation working correctly!")
        print(f"{'='*80}\n")

        print("Working token for API requests:")
        print(f"Authorization: Bearer {token}\n")

        return token

    except jwt.InvalidTokenError as e:
        print(f"ERROR decoding token: {e}")
        print(f"Error type: {type(e).__name__}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        return None


if __name__ == "__main__":
    test_jwt_round_trip()
