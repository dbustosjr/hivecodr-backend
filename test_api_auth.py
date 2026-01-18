"""Test the /api/generate endpoint authentication."""

import httpx
import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
API_URL = "http://localhost:8000/api/generate"

def generate_token():
    """Generate a fresh JWT token."""
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

    token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
    return token


def test_api_authentication():
    """Test API authentication with JWT token."""

    print(f"\n{'='*80}")
    print("Testing API Authentication")
    print(f"{'='*80}\n")

    # Generate fresh token
    token = generate_token()
    print(f"Generated token (first 50 chars): {token[:50]}...")
    print(f"Token length: {len(token)}")
    print(f"Token type: {type(token)}")

    # Check for whitespace
    if token != token.strip():
        print("WARNING: Token has leading/trailing whitespace!")
    else:
        print("Token has no extra whitespace")
    print()

    # Prepare request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "requirements": "Create a simple user API with name and email fields"
    }

    print(f"Endpoint: {API_URL}")
    print(f"Authorization header: Bearer {token[:30]}...")
    print(f"\nSending request...\n")

    try:
        # Use longer timeout for two-agent workflow (takes 2-5 minutes)
        with httpx.Client(timeout=600.0) as client:
            response = client.post(API_URL, headers=headers, json=payload)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}\n")

        if response.status_code == 200:
            print("SUCCESS: Authentication worked!")
            result = response.json()
            print(f"Generation ID: {result.get('id')}")
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")

    except httpx.ConnectError:
        print("ERROR: Could not connect to server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}")
        print(f"Message: {str(e)}")


if __name__ == "__main__":
    test_api_authentication()
