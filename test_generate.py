"""Test script for the /api/generate endpoint."""

import httpx
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/generate"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZmVkNzViZC0zNTMxLTRmZGUtYjY1Ny04ZmVjYTZkZDUwYjEiLCJlbWFpbCI6InRlc3RAaGl2ZWNvZHIuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiaWF0IjoxNzY4NTQyMTIyLCJleHAiOjE3Njg2Mjg1MjJ9.rLL4CdRjlJ1KdSX-FRpkOaHGUfcV-t0mSAvhtt-EHEo"

# Test prompt
REQUIREMENTS = "Create a simple blog post API with CRUD operations"


def test_generate_endpoint():
    """Test the /api/generate endpoint."""

    print(f"\n{'='*80}")
    print("Testing HiveCodr /api/generate Endpoint")
    print(f"{'='*80}\n")

    print(f"Endpoint: {API_URL}")
    print(f"Requirements: {REQUIREMENTS}")
    print(f"\nSending request...\n")

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "requirements": REQUIREMENTS
    }

    try:
        # Send POST request
        with httpx.Client(timeout=300.0) as client:  # 5 minute timeout for AI generation
            response = client.post(API_URL, headers=headers, json=payload)

        print(f"Status Code: {response.status_code}")
        print(f"{'='*80}\n")

        if response.status_code == 200:
            result = response.json()

            print("SUCCESS!\n")
            print(f"Generation ID: {result.get('id')}")
            print(f"Created At: {result.get('created_at')}")
            print(f"\n{'='*80}")
            print("AGENT LOG:")
            print(f"{'='*80}")
            print(result.get('agent_log', 'No log available'))
            print(f"\n{'='*80}")
            print("GENERATED CODE:")
            print(f"{'='*80}\n")

            # Pretty print the generated code
            code = result.get('code', {})
            for filename, content in code.items():
                print(f"\n--- {filename} ---")
                print(content)
                print(f"--- End of {filename} ---\n")

            # Save to file for easier viewing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"generation_output_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\n{'='*80}")
            print(f"Full output saved to: {output_file}")
            print(f"{'='*80}\n")

        else:
            print("ERROR!\n")
            print(f"Response: {response.text}")

    except httpx.TimeoutException:
        print("\nRequest timed out!")
        print("The AI generation is taking longer than expected.")
        print("This might be normal for complex requirements.")

    except httpx.ConnectError:
        print("\nConnection Error!")
        print("Make sure the server is running on http://localhost:8000")
        print("Run: python main.py")

    except Exception as e:
        print(f"\nUnexpected Error!")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_generate_endpoint()
