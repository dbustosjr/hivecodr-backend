"""Test script for fitness tracking app generation with file-based architecture."""

import httpx
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/generate"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZmVkNzViZC0zNTMxLTRmZGUtYjY1Ny04ZmVjYTZkZDUwYjEiLCJlbWFpbCI6InRlc3RAaGl2ZWNvZHIuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiaWF0IjoxNzY4NjIzMjk2LCJleHAiOjE3Njg3MDk2OTZ9.GD9jsbT9KCeHr4Yg0e_11DSIl5XZYLFQu0zOqI5D-n8"

# Fitness tracking app requirements
REQUIREMENTS = """
Create a fitness tracking app with workouts, exercises, and progress tracking.

Features needed:
- Users can create and manage workout routines
- Each workout contains multiple exercises
- Track sets, reps, and weight for each exercise
- Record workout sessions with date and duration
- View progress over time with charts
- Set fitness goals and track achievements
"""


def test_fitness_app_generation():
    """Test fitness app generation with file-based architecture."""

    print(f"\n{'='*80}")
    print("Testing Fitness App Generation with File-Based Architecture")
    print(f"{'='*80}\n")

    print(f"Endpoint: {API_URL}")
    print(f"\nRequirements:")
    print(f"{REQUIREMENTS}")
    print(f"\nSending request...")
    print("This will generate files directly to disk instead of returning code in JSON")
    print()

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "requirements": REQUIREMENTS
    }

    try:
        print(f"Starting at: {datetime.now().strftime('%H:%M:%S')}\\n")

        with httpx.Client(timeout=600.0) as client:  # 10 minute timeout
            response = client.post(API_URL, headers=headers, json=payload)

        print(f"\nCompleted at: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Status Code: {response.status_code}")
        print(f"{'='*80}\\n")

        if response.status_code == 200:
            result = response.json()

            print("SUCCESS!\\n")
            print(f"Generation ID: {result.get('id')}")
            print(f"Created At: {result.get('created_at')}")

            # Display output directory and file information
            code_info = result.get('code', {})
            output_dir = code_info.get('output_directory', 'N/A')

            print(f"\n{'='*80}")
            print("OUTPUT DIRECTORY:")
            print(f"{'='*80}")
            print(f"All generated files written to: {output_dir}")

            # Display backend files
            backend_stats = code_info.get('backend', {})
            print(f"\n{'='*80}")
            print("BACKEND FILES:")
            print(f"{'='*80}")
            if backend_stats:
                for filename, stats in backend_stats.items():
                    print(f"  {filename}.py:")
                    print(f"    - Path: {stats.get('path', 'N/A')}")
                    print(f"    - Lines: {stats.get('lines', 0)}")
                    print(f"    - Characters: {stats.get('chars', 0)}")
            else:
                print("  No backend files information available")

            # Display frontend files
            frontend_stats = code_info.get('frontend', {})
            print(f"\n{'='*80}")
            print("FRONTEND FILES:")
            print(f"{'='*80}")
            if frontend_stats:
                total_files = len(frontend_stats)
                print(f"  Total files: {total_files}")

                # Group by type
                config_files = [f for f in frontend_stats.keys() if f.endswith(('.json', '.ts', '.js')) and '/' not in f]
                app_files = [f for f in frontend_stats.keys() if f.startswith('app/')]
                component_files = [f for f in frontend_stats.keys() if f.startswith('components/')]
                lib_files = [f for f in frontend_stats.keys() if f.startswith('lib/')]

                if config_files:
                    print(f"\n  Configuration files ({len(config_files)}):")
                    for f in config_files:
                        stats = frontend_stats[f]
                        print(f"    - {f}: {stats.get('lines', 0)} lines")

                if app_files:
                    print(f"\n  App files ({len(app_files)}):")
                    for f in app_files[:10]:  # Show first 10
                        stats = frontend_stats[f]
                        print(f"    - {f}: {stats.get('lines', 0)} lines")
                    if len(app_files) > 10:
                        print(f"    ... and {len(app_files) - 10} more")

                if component_files:
                    print(f"\n  Component files ({len(component_files)}):")
                    for f in component_files[:10]:
                        stats = frontend_stats[f]
                        print(f"    - {f}: {stats.get('lines', 0)} lines")
                    if len(component_files) > 10:
                        print(f"    ... and {len(component_files) - 10} more")

                if lib_files:
                    print(f"\n  Library files ({len(lib_files)}):")
                    for f in lib_files:
                        stats = frontend_stats[f]
                        print(f"    - {f}: {stats.get('lines', 0)} lines")
            else:
                print("  No frontend files information available")

            # Show total stats
            print(f"\n{'='*80}")
            print("SUMMARY:")
            print(f"{'='*80}")
            print(f"- Output directory: {output_dir}")
            print(f"- Backend files: {len(backend_stats)}")
            print(f"- Frontend files: {len(frontend_stats)}")
            print(f"- Total files: {len(backend_stats) + len(frontend_stats)}")
            print(f"\nAll files have been written to disk!")
            print(f"You can now navigate to the output directory to see the generated code.")

        else:
            print("ERROR!\\n")
            print(f"Response: {response.text}")

    except httpx.TimeoutException:
        print("\nRequest timed out!")
        print("The generation is taking longer than expected.")

    except httpx.ConnectError:
        print("\nConnection Error!")
        print("Make sure the server is running on http://localhost:8000")

    except Exception as e:
        print(f"\nUnexpected Error!")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_fitness_app_generation()
