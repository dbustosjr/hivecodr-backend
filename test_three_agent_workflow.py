"""Test script for the three-agent sequential workflow (Architect + Developer + Frontend Bee)."""

import httpx
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/generate"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZmVkNzViZC0zNTMxLTRmZGUtYjY1Ny04ZmVjYTZkZDUwYjEiLCJlbWFpbCI6InRlc3RAaGl2ZWNvZHIuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiaWF0IjoxNzY4NjIzMjk2LCJleHAiOjE3Njg3MDk2OTZ9.GD9jsbT9KCeHr4Yg0e_11DSIl5XZYLFQu0zOqI5D-n8"

# Test prompt - simpler blog app to test three-agent workflow
REQUIREMENTS = """
Create a simple blog with posts and comments
"""


def test_three_agent_workflow():
    """Test the three-agent sequential workflow."""

    print(f"\n{'='*80}")
    print("Testing Three-Agent Workflow: Architect + Developer + Frontend Bee")
    print(f"{'='*80}\n")

    print(f"Endpoint: {API_URL}")
    print(f"\nRequirements:")
    print(f"{REQUIREMENTS}")
    print(f"\nSending request...\n")
    print("This will take 6-10 minutes as THREE agents work sequentially:")
    print("  1. Architect Bee - Designs the architecture")
    print("  2. Developer Bee - Generates the backend code")
    print("  3. Frontend Bee - Generates the Next.js frontend")
    print()

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "requirements": REQUIREMENTS
    }

    try:
        # Send POST request with extended timeout for three-agent workflow
        print(f"Starting at: {datetime.now().strftime('%H:%M:%S')}\n")

        with httpx.Client(timeout=600.0) as client:  # 10 minute timeout
            response = client.post(API_URL, headers=headers, json=payload)

        print(f"\nCompleted at: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Status Code: {response.status_code}")
        print(f"{'='*80}\n")

        if response.status_code == 200:
            result = response.json()

            print("SUCCESS!\n")
            print(f"Generation ID: {result.get('id')}")
            print(f"Created At: {result.get('created_at')}")

            # Display backend code summary
            backend_code = result.get('code', {}).get('backend', {})
            print(f"\n{'='*80}")
            print("BACKEND CODE GENERATED:")
            print(f"{'='*80}")
            print(f"Files: {', '.join(backend_code.keys())}")
            for filename, content in backend_code.items():
                lines = content.split('\n') if content else []
                print(f"  - {filename}: {len(lines)} lines")

            # Display frontend code summary
            frontend_code = result.get('code', {}).get('frontend', {})
            print(f"\n{'='*80}")
            print("FRONTEND CODE GENERATED:")
            print(f"{'='*80}")
            print(f"Total files: {len(frontend_code)}")

            # Group files by type
            config_files = [f for f in frontend_code.keys() if f.endswith(('.json', '.ts', '.js')) and '/' not in f]
            app_files = [f for f in frontend_code.keys() if f.startswith('app/')]
            component_files = [f for f in frontend_code.keys() if f.startswith('components/')]
            lib_files = [f for f in frontend_code.keys() if f.startswith('lib/')]

            print(f"  - Configuration files: {len(config_files)}")
            for f in config_files:
                print(f"    • {f}")

            print(f"  - App files: {len(app_files)}")
            if len(app_files) <= 10:
                for f in app_files:
                    print(f"    • {f}")
            else:
                for f in app_files[:5]:
                    print(f"    • {f}")
                print(f"    ... and {len(app_files) - 5} more")

            print(f"  - Component files: {len(component_files)}")
            if len(component_files) <= 10:
                for f in component_files:
                    print(f"    • {f}")
            else:
                for f in component_files[:5]:
                    print(f"    • {f}")
                print(f"    ... and {len(component_files) - 5} more")

            print(f"  - Library files: {len(lib_files)}")
            for f in lib_files:
                print(f"    • {f}")

            # Extract and display the agent logs
            agent_log = result.get('agent_log', '')

            print(f"\n{'='*80}")
            print("AGENT WORKFLOW LOG:")
            print(f"{'='*80}")

            # Show all three phases
            if "PHASE 1: ARCHITECTURE DESIGN" in agent_log:
                phase1_start = agent_log.find("PHASE 1: ARCHITECTURE DESIGN")
                phase2_start = agent_log.find("PHASE 2: BACKEND CODE GENERATION")
                phase3_start = agent_log.find("PHASE 3: FRONTEND CODE GENERATION")

                if phase2_start > phase1_start:
                    print("\n--- PHASE 1: ARCHITECT BEE ---")
                    phase1_log = agent_log[phase1_start:phase2_start].strip()
                    if len(phase1_log) > 1000:
                        print(f"{phase1_log[:1000]}...")
                        print(f"\n[Truncated - {len(phase1_log)} total characters]")
                    else:
                        print(phase1_log)

                if phase3_start > phase2_start:
                    print("\n--- PHASE 2: DEVELOPER BEE ---")
                    phase2_log = agent_log[phase2_start:phase3_start].strip()
                    if len(phase2_log) > 1000:
                        print(f"{phase2_log[:1000]}...")
                        print(f"\n[Truncated - {len(phase2_log)} total characters]")
                    else:
                        print(phase2_log)

                    print("\n--- PHASE 3: FRONTEND BEE ---")
                    phase3_log = agent_log[phase3_start:].strip()
                    if len(phase3_log) > 1000:
                        print(f"{phase3_log[:1000]}...")
                        print(f"\n[Truncated - {len(phase3_log)} total characters]")
                    else:
                        print(phase3_log)
            else:
                print(agent_log[:3000] if len(agent_log) > 3000 else agent_log)

            # Save to file for easier viewing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"three_agent_output_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"\n{'='*80}")
            print(f"Full output saved to: {output_file}")
            print(f"{'='*80}\n")

            # Summary
            print(f"\nSUMMARY:")
            print(f"- Three-agent workflow completed successfully")
            print(f"- Architecture designed by Architect Bee")
            print(f"- Backend code generated by Developer Bee ({len(backend_code)} files)")
            print(f"- Frontend code generated by Frontend Bee ({len(frontend_code)} files)")
            print(f"- Total files generated: {len(backend_code) + len(frontend_code)}")
            print(f"\nYou now have a complete full-stack fitness tracking application!")

        else:
            print("ERROR!\n")
            print(f"Response: {response.text}")

    except httpx.TimeoutException:
        print("\nRequest timed out!")
        print("The three-agent workflow is taking longer than expected.")
        print("This might be normal for complex requirements.")

    except httpx.ConnectError:
        print("\nConnection Error!")
        print("Make sure the server is running on http://localhost:8000")

    except Exception as e:
        print(f"\nUnexpected Error!")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_three_agent_workflow()
