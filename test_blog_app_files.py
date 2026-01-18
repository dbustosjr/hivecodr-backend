"""Test script for simple blog generation with file-based architecture."""

import httpx
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/generate"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZmVkNzViZC0zNTMxLTRmZGUtYjY1Ny04ZmVjYTZkZDUwYjEiLCJlbWFpbCI6InRlc3RAaGl2ZWNvZHIuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiaWF0IjoxNzY4NjIzMjk2LCJleHAiOjE3Njg3MDk2OTZ9.GD9jsbT9KCeHr4Yg0e_11DSIl5XZYLFQu0zOqI5D-n8"

# Simple blog requirements
REQUIREMENTS = "Create a simple blog with posts and comments"


def test_blog_generation():
    """Test blog generation with file-based architecture."""

    print(f"\n{'='*80}")
    print("Testing Simple Blog Generation with File-Based Architecture")
    print(f"{'='*80}\n")

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "requirements": REQUIREMENTS
    }

    try:
        print(f"Starting at: {datetime.now().strftime('%H:%M:%S')}\\n")

        with httpx.Client(timeout=600.0) as client:
            response = client.post(API_URL, headers=headers, json=payload)

        print(f"\\nCompleted at: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Status Code: {response.status_code}\\n")

        if response.status_code == 200:
            result = response.json()
            code_info = result.get('code', {})
            output_dir = code_info.get('output_directory', 'N/A')

            print(f"SUCCESS! Output: {output_dir}")
            print(f"Backend files: {len(code_info.get('backend', {}))}")
            print(f"Frontend files: {len(code_info.get('frontend', {}))}")
        else:
            print(f"ERROR: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_blog_generation()
